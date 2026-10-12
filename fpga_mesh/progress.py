"""Local progress observations without inference or task-state mutation."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from .protocol import MessageKind


STATES = ("running", "queued", "failed", "interrupted", "completed", "unknown")
NON_WORK = {MessageKind.STATUS_QUERY, MessageKind.STOP_REQUEST, MessageKind.RESUME_REQUEST}


def progress_snapshot(runtime) -> dict:
    controller = runtime.controller
    active = controller.active_snapshot()
    snapshot = {
        "node_id": runtime.config.node_id,
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "paused": controller.dispatch_blocked,
        "active_dispatch": active,
        "pending_inbound": "unknown",
        "pending_work": "unknown", "pending_queries": "unknown", "pending_controls": "unknown",
        "main": {"counts": "unknown", "recent": [], "basis": "local ledger and controller"},
        "children": {"counts": "unknown", "basis": "ledger only; live process state unverified"},
        "completion_percent": "unknown", "remote_progress": "unknown",
    }
    try:
        inbound = runtime.store.inbound_progress()
        snapshot["pending_inbound"] = len(inbound)
        snapshot["pending_queries"] = sum(row.message.kind == MessageKind.STATUS_QUERY for row in inbound)
        snapshot["pending_controls"] = sum(row.message.kind in {MessageKind.STOP_REQUEST, MessageKind.RESUME_REQUEST}
                                            for row in inbound)
        pending = {row.message.message_id: row for row in inbound
                   if row.message.kind not in NON_WORK}
        snapshot["pending_work"] = len(pending)
        records = {row["message_id"]: dict(row, ledger_status=row["status"])
                   for row in runtime.main_sessions.run_summaries()}
        current = datetime.now(timezone.utc)
        for identity, row in pending.items():
            if identity not in records:
                records[identity] = {
                    "message_id": identity, "task_id": row.message.task_id,
                    "status": "failed" if row.last_error else "queued",
                    "ledger_status": "unknown", "updated_at": row.message.sent_at.isoformat(),
                }
            records[identity]["retry_at"] = (row.next_attempt_at.isoformat()
                                               if row.next_attempt_at else None)
            records[identity]["inbox_pending"] = True
            if row.message.expires_at and row.message.expires_at <= current:
                if records[identity]["status"] in {"queued", "running"}:
                    records[identity]["status"] = "unknown"
        for identity, row in records.items():
            if row["status"] not in STATES:
                row["status"] = "unknown"
            if row["status"] == "running" and identity != active["message_id"]:
                row["status"] = "unknown"
            if row["status"] == "queued" and identity not in pending:
                row["status"] = "unknown"
            if identity == active["message_id"] and row["status"] not in {"failed", "interrupted", "completed"}:
                row["status"] = "running" if active["state"] == "running" else "unknown"
        counts = Counter(row["status"] for row in records.values())
        # Active work is first, then latest observed entries. Counts cover all history.
        recent = sorted(records.values(), key=lambda row: (
            row["message_id"] == active["message_id"], row["updated_at"]), reverse=True)
        snapshot["main"].update(counts={state: counts[state] for state in STATES}, recent=recent[:10],
                                total_records=len(records))
    except Exception:  # noqa: BLE001 - an unavailable source is unknown, not zero
        pass
    try:
        counts = Counter(str(job["status"]) for job in runtime.children.status()["jobs"])
        snapshot["children"]["counts"] = dict(sorted(counts.items()))
    except Exception:  # noqa: BLE001 - do not expose exception text to the group
        pass
    return snapshot


def format_progress(snapshot: dict) -> str:
    def counts(value):
        return "unknown" if value == "unknown" else ", ".join(f"{k}={v}" for k, v in value.items()) or "none"
    active = snapshot["active_dispatch"]
    lines = [
        f"Astra-{snapshot['node_id']} 本机只读状态 · snapshot_at={snapshot['snapshot_at']}",
        f"paused={str(snapshot['paused']).lower()}; active_dispatch={active['state']}",
        f"pending_inbound={snapshot['pending_inbound']}; pending_work={snapshot['pending_work']}; "
        f"pending_queries={snapshot['pending_queries']}; pending_controls={snapshot['pending_controls']} (含退避等待)",
        f"main 历史记录计数: {counts(snapshot['main']['counts'])}",
        f"children 账本计数 (未验证进程): {counts(snapshot['children']['counts'])}",
        "completion_percent=unknown; remote_progress=unknown",
    ]
    if active["message_id"]:
        lines.append(f"active_task={str(active['task_id'])[:180]}")
    for row in snapshot["main"]["recent"]:
        retry = f"; inbox_pending=true; retry_at={row.get('retry_at')}" if row.get("inbox_pending") else ""
        lines.append(f"{row['status']}: {str(row['task_id'])[:180]} (ledger={row['ledger_status']}; updated_at={row['updated_at']}{retry})")
    lines.append("running 表示活动分派；完成率未知。failed/interrupted 主回合不自动重放；入站待处理项可能等待重试判定或归档。")
    return "\n".join(lines)
