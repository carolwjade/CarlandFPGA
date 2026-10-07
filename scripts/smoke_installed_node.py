"""Verify a deployed node config with a real child request."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from fpga_mesh.child_control import LocalControlFileClient
from fpga_mesh.runtime import NodeConfig, NodeRuntime


async def main(config_path: Path) -> None:
    config = NodeConfig.load(config_path)
    if config.mode != "app_server":
        raise RuntimeError("installed config must use app_server mode")
    discovery = config.state_dir / "child-control.json"
    if discovery.exists():
        client = LocalControlFileClient(discovery)
        before = await client.call("status", {})
        job = await client.call("delegate", {
            "task_id": "installed-smoke", "task_version": 1,
            "text": "Reply with exactly DEPLOYED_OK.",
        })
        result = (await client.call("wait", {"job_ids": [job["job_id"]]}))[0]
        after = await client.call("status", {})
        if (result["status"] != "completed"
                or (result["result"] or {}).get("text", "").strip() != "DEPLOYED_OK"):
            raise RuntimeError("deployed child did not return DEPLOYED_OK")
        print(json.dumps({
            "node_id": config.node_id,
            "mode": config.mode,
            "attached_to_running_service": True,
            "initial_standby": before["pool"].get("standby"),
            "status": result["status"],
            "result_text": (result["result"] or {}).get("text"),
            "final_standby": after["pool"].get("standby"),
        }, ensure_ascii=True))
        return
    runtime = NodeRuntime(config)
    await runtime.start()
    try:
        before = runtime.snapshot()
        job = await runtime.children.delegate(
            task_id="installed-smoke", task_version=1,
            text="Reply with exactly DEPLOYED_OK.",
        )
        result = (await runtime.children.wait([job["job_id"]]))[0]
        if (result["status"] != "completed"
                or (result["result"] or {}).get("text", "").strip() != "DEPLOYED_OK"):
            raise RuntimeError("standalone child did not return DEPLOYED_OK")
        print(json.dumps({
            "node_id": config.node_id,
            "mode": config.mode,
            "initial_standby": before["pool"].get("standby"),
            "status": result["status"],
            "result_text": (result["result"] or {}).get("text"),
            "final_standby": runtime.snapshot()["pool"].get("standby"),
        }, ensure_ascii=True))
    finally:
        await runtime.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(main(args.config))
