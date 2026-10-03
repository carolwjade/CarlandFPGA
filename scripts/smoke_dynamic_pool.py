"""Exercise real concurrent DeepSeek expansion beyond two standby children."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from fpga_mesh.runtime import NodeConfig, NodeRuntime


async def main(config_path: Path) -> None:
    config = NodeConfig.load(config_path)
    runtime = NodeRuntime(config)
    await runtime.start()
    try:
        jobs = await asyncio.gather(*(
            runtime.children.delegate(
                task_id=f"pool-smoke-{index}", task_version=1,
                text=f"Reply with exactly CHILD_{index}.", auto_expand=True,
            ) for index in range(1, 4)
        ))
        results = await runtime.children.wait([job["job_id"] for job in jobs])
        before = runtime.pool.snapshot()
        await runtime.children.scale(2)
        after = runtime.pool.snapshot()
        print(json.dumps({
            "distinct_ids": len({j["instance_id"] for j in jobs}) == 3,
            "all_max": {i["reasoning_effort"] for i in before["instances"]} == {"max"},
            "results": [j["result"]["text"] if j["result"] else None
                        for j in results],
            "statuses": [j["status"] for j in results],
            "expanded_to": len(before["instances"]),
            "restored_to": len(after["instances"]),
        }, ensure_ascii=True))
    finally:
        await runtime.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(main(args.config))
