"""Verify a deployed node config with a real child request."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from fpga_mesh.runtime import NodeConfig, NodeRuntime


async def main(config_path: Path) -> None:
    config = NodeConfig.load(config_path)
    if config.mode != "app_server":
        raise RuntimeError("installed config must use app_server mode")
    runtime = NodeRuntime(config)
    await runtime.start()
    try:
        before = runtime.snapshot()
        job = await runtime.children.delegate(
            task_id="installed-smoke", task_version=1,
            text="Reply with exactly DEPLOYED_OK.",
        )
        result = (await runtime.children.wait([job["job_id"]]))[0]
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
