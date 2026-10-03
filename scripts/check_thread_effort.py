"""Read persisted model effort for a Codex thread without starting a turn."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from fpga_mesh.app_server import AppServerClient


async def main(thread_id: str) -> None:
    client = await AppServerClient.start_stdio(
        codex_home=Path.home() / ".codex", client_version="0.160.0",
        role="astra",
    )
    try:
        await client.initialize()
        result = await client.session.request(
            "thread/read", {"threadId": thread_id, "includeTurns": False},
        )
        thread = result["thread"]
        print(json.dumps({
            "thread_id": thread["id"], "model": thread.get("model"),
            "reasoning_effort": thread.get("reasoningEffort"),
            "status": thread.get("status"),
        }, ensure_ascii=True))
    finally:
        await client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("thread_id")
    args = parser.parse_args()
    asyncio.run(main(args.thread_id))
