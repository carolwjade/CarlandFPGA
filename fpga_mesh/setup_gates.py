"""Evidence-based teammate setup report; it never reads or emits credentials."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path
from typing import Any

from .http_transport import HttpPeer
from .runtime import NodeConfig


def human_roundtrip_verified(database: Path) -> bool:
    if not database.is_file():
        return False
    try:
        with closing(sqlite3.connect(
            f"file:{database.resolve().as_posix()}?mode=ro", uri=True,
        )) as conn:
            return conn.execute("""
                SELECT 1 FROM inbound AS i JOIN group_outbox AS g
                  ON g.operation_id LIKE 'result:' || i.message_id || ':%'
                WHERE i.message_id LIKE 'feishu:%'
                  AND i.processed_at IS NOT NULL AND g.sent_at IS NOT NULL
                LIMIT 1
            """).fetchone() is not None
    except (OSError, sqlite3.Error):
        return False


def _command(*args: str, timeout: float = 10) -> str | None:
    try:
        result = subprocess.run(args, capture_output=True, text=True,
                                check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _has_nonempty_file(path: Path | None) -> bool:
    return path is not None and path.is_file() and path.stat().st_size > 0


def child_smoke_verified(result: dict[str, Any], revision: str | None) -> bool:
    """Accept only a real completed parent/child result from this checkout."""
    return bool(
        revision and result.get("revision") == revision
        and result.get("parent_accepted") is True
        and result.get("parent_text", "").strip() == "CHILD_OK"
        and result.get("parent_effort") in {"low", "medium", "high", "xhigh", "max", "ultra"}
        and any(job.get("status") == "completed"
                and job.get("result_text", "").strip() == "CHILD_OK"
                for job in result.get("child_jobs", []))
        and result.get("pool_efforts") == ["max"]
    )


def collect_facts(workspace: Path, node: str) -> dict[str, Any]:
    """Probe a local node without changing remote accounts or exposing secrets."""
    root = workspace.resolve()
    node_root = root / ".local" / "deployment" / f"node-{node.lower()}"
    config_path = node_root / f"node-{node.lower()}.toml"
    config = NodeConfig.load(config_path) if config_path.is_file() else None
    git_read = _command("git", "-C", str(root), "ls-remote", "upstream",
                        "refs/heads/main")
    if not git_read:
        git_read = _command("git", "-C", str(root), "ls-remote", "origin",
                            "refs/heads/main")
    github_auth = _command("gh", "auth", "status") is not None
    upstream_write = False
    fork_ready = False
    if github_auth:
        upstream_write = _command(
            "gh", "api", "repos/carolwjade/CarlandFPGA",
            "--jq", ".permissions.push",
        ) == "true"
        login = _command("gh", "api", "user", "--jq", ".login")
        if login:
            fork_ready = bool(_command(
                "gh", "api", f"repos/{login}/CarlandFPGA", "--jq", ".full_name",
            ))
    tail_ip = _command("tailscale", "ip", "-4") or ""
    tail_ip = next((line for line in tail_ip.splitlines()
                    if line.startswith("100.")), "")
    peers = config.peer_urls if config else {}
    secret_path = config.peer_shared_secret_file if config else None
    secret_ok = _has_nonempty_file(secret_path)
    peer_health: dict[str, bool] = {}
    if config and secret_ok:
        probe = HttpPeer(node_id=node, project_id=config.project_id,
                         store=None, controller=None, peer_urls=peers,
                         shared_secret=secret_path.read_text(encoding="utf-8-sig").strip())
        peer_health = {peer: probe._probe(url, peer) for peer, url in peers.items()}
    facts: dict[str, Any] = {
        "node": node,
        "source_read": bool(git_read),
        "github_auth": github_auth,
        "upstream_write": upstream_write,
        "fork_ready": fork_ready,
        "codex_auth": _command("codex", "login", "status") is not None,
        "deepseek_key": bool(config and _has_nonempty_file(config.deepseek_key_file)),
        "tailscale_ip": tail_ip,
        "shared_secret": secret_ok,
        "peer_urls": peers,
        "peer_health": peer_health,
        "service_running": _command(
            "powershell", "-NoProfile", "-Command",
            f"(Get-ScheduledTask -TaskName 'FPGA-Mesh-Node-{node}' -ErrorAction SilentlyContinue).State.ToString()",
        ) == "Running",
        "human_roundtrip": bool(config and human_roundtrip_verified(
            config.state_dir / "state.sqlite")),
    }
    for role in ("astra", "deepseek"):
        app_id = getattr(config, f"feishu_{role}_app_id", "") if config else ""
        manifest = node_root / "feishu" / f"{role}.json"
        if not app_id and manifest.is_file():
            try:
                app_id = str(json.loads(manifest.read_text(encoding="utf-8"))["app_id"])
            except (OSError, ValueError, KeyError):
                app_id = ""
        receipt = node_root / "feishu" / f"{role}-selftest.json"
        try:
            state = json.loads(receipt.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
        facts[f"{role}_app_id"] = app_id
        facts[f"{role}_verified"] = bool(
            state.get("verified") is True and state.get("app_id") == app_id
            and config is not None and state.get("group_id") == config.feishu_group_id
            and state.get("message_id")
        )
    smoke = node_root / "parent-child-smoke.json"
    try:
        result = json.loads(smoke.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        result = {}
    revision = _command("git", "-C", str(root), "rev-parse", "HEAD")
    facts["child_route"] = child_smoke_verified(result, revision)
    return facts


def assess_setup(facts: dict[str, Any]) -> dict[str, Any]:
    node = str(facts.get("node", ""))
    if node not in {"A", "B", "C"}:
        raise ValueError("node must be A, B, or C")
    peers = sorted({"A", "B", "C"} - {node})
    gates: list[dict[str, str]] = []

    def need(ok: bool, code: str, action: str) -> None:
        if not ok:
            gates.append({"code": code, "action": action})

    need(bool(facts.get("source_read")), "source_read",
         "安装 Git 并从 https://github.com/carolwjade/CarlandFPGA 克隆或更新源码。")
    need(bool(facts.get("github_auth")), "github_auth",
         "用自己的 GitHub 账号完成 `gh auth login --web`；不要共用 A 机令牌。")
    need(bool(facts.get("fork_ready") or facts.get("upstream_write")), "code_write",
         "登录后建立个人 fork 并配置 origin/upstream；或由仓库所有者授予 collaborator 权限。")
    need(bool(facts.get("upstream_write")), "upstream_write",
         "请仓库所有者在 https://github.com/carolwjade/CarlandFPGA/settings/access 邀请当前 GitHub 用户为 collaborator。获得上游写权限前可用 fork/PR 提交代码，但不能写入共享认领分支；未指派的群任务不可声称已独占。")
    need(bool(facts.get("codex_auth")), "codex_auth",
         "在本机 Codex 中登录自己的 ChatGPT/Codex 订阅，并核验 `codex login status`。")
    need(bool(facts.get("deepseek_key")), "deepseek_key",
         "将自己的 DeepSeek API key 存在本机文件中，只向部署脚本提供文件路径；不要发群、提交 Git 或写入 ZIP。")
    need(bool(facts.get("tailscale_ip")), "tailscale_login",
         "安装并登录 Tailscale，加入三人共用的 tailnet；以 `tailscale ip -4` 核实本机 100.x 地址。")
    need(bool(facts.get("shared_secret")), "shared_secret",
         "经可信渠道从团队获取同一 HMAC 共享密钥文件并保存在本机，不能通过公开 Git 或飞书群发送内容。")
    configured_peers = facts.get("peer_urls") or {}
    health = facts.get("peer_health") or {}
    for peer in peers:
        need(bool(configured_peers.get(peer)), f"peer_url_{peer}",
             f"取得 {peer} 机的 Tailscale 100.x 地址，配置 `http://<地址>:8787`；不经过 A 中转。")
        need(health.get(peer) is True, f"peer_{peer}",
             f"在两机在线时运行带 HMAC 的 {peer} 机健康探针；离线时记录未验收并继续本机工作。")

    for role in ("astra", "deepseek"):
        label = "Astra" if role == "astra" else "DeepSeek"
        app_id = str(facts.get(f"{role}_app_id") or "")
        if not app_id.startswith("cli_"):
            need(False, f"{role}_registration",
                 f"在飞书开发者平台 https://open.feishu.cn/ 创建本机 FPGA {label} {node} 应用；按设备授权提示由账号本人扫码。")
        if facts.get(f"{role}_verified") is not True:
            portal = (f"https://open.feishu.cn/app/{app_id}/version"
                      if app_id.startswith("cli_") else "https://open.feishu.cn/")
            need(False, f"{role}_selftest",
                 f"检查 {label} 应用权限和版本 {portal}；外部群开关灰色时由本人完成飞书个人实名认证。发布允许机器人加入外部群的版本，在 FPGA/AI/DEV → 设置 → Bots → Add Bot 加入该机器人；然后重跑同身份发信及同消息 ID/群 ID/正文读回自测。")
    need(bool(facts.get("service_running")), "service_running",
         f"登录和本机密钥就绪后注册并启动 `FPGA-Mesh-Node-{node}`，再用真人 `/fpga {node}` 群消息验收 Astra 接收与回报。")
    need(bool(facts.get("human_roundtrip")), "human_roundtrip",
         f"请真人在 FPGA/AI/DEV 发 `/fpga {node} 链路自测：只回复 ACK_<随机标记>`；核对本机入站处理记录和群内 Astra 回复，不能只凭长连接成功宣称接收完成。")
    need(bool(facts.get("child_route")), "child_route",
         "从本机 Codex 运行一次真实 Astra→DeepSeek V4.1 Flash 委派，等待持久子结果；核对主模型动态推理档位和子模型 `max`，保存非秘密回执。")
    return {
        "node": node,
        "ready": not gates,
        "capabilities": {
            "source_read": bool(facts.get("source_read")),
            "code_contribution": bool(facts.get("github_auth") and
                                      (facts.get("fork_ready") or facts.get("upstream_write"))),
            "shared_task_claims": bool(facts.get("upstream_write")),
            "feishu_astra": facts.get("astra_verified") is True,
            "feishu_deepseek": facts.get("deepseek_verified") is True,
            "peer_health": {peer: health.get(peer) is True for peer in peers},
        },
        "gates": gates,
    }


def render_next_steps(report: dict[str, Any]) -> str:
    node = report["node"]
    lines = [
        f"# FPGA Mesh {node} 机接入状态",
        "",
        "完整上线：" + ("已按本次证据通过" if report["ready"] else "尚未通过；可继续独立工作"),
        "",
        "以下事项由本机 Codex 自动推进；涉及账号本人、所有者授权或密钥交换时，显示对应页面并等待人操作。操作完成后重跑 `deploy/Join-FPGAMesh.ps1 -Node " + node + "`。",
        "逐屏操作见仓库 `deploy/HUMAN_STEPS.md`；此报告位于被 Git 忽略的本机目录，不含密钥。",
        "",
    ]
    if report["gates"]:
        lines.extend(f"- [ ] {item['action']}" for item in report["gates"])
    else:
        lines.append("- [x] 当前清单无剩余门槛；继续监控运行与实际任务结果。")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render credential-free setup gates")
    parser.add_argument("--facts", type=Path)
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--node", choices="ABC")
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-markdown", type=Path, required=True)
    args = parser.parse_args()
    if args.facts is not None:
        facts = json.loads(args.facts.read_text(encoding="utf-8-sig"))
    elif args.workspace is not None and args.node is not None:
        facts = collect_facts(args.workspace, args.node)
    else:
        parser.error("provide --facts or both --workspace and --node")
    report = assess_setup(facts)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    args.output_markdown.write_text(render_next_steps(report), encoding="utf-8")
    print(json.dumps({"node": report["node"], "ready": report["ready"],
                      "gate_codes": [gate["code"] for gate in report["gates"]]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
