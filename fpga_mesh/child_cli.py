"""Stable shell entry point for an Astra that lacks a dynamic MCP tool catalog."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .child_control import LocalControlFileClient


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="fpga-mesh-child")
    top.add_argument("--control-file", type=Path, required=True)
    sub = top.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    scale = sub.add_parser("scale")
    scale.add_argument("count", type=int)
    delegate = sub.add_parser("delegate")
    delegate.add_argument("--task-id", required=True)
    delegate.add_argument("--task-version", type=int, required=True)
    content = delegate.add_mutually_exclusive_group(required=True)
    content.add_argument("--text")
    content.add_argument("--text-file", type=Path)
    delegate.add_argument("--instance-id")
    delegate.add_argument("--auto-expand", action="store_true")
    wait = sub.add_parser("wait")
    wait.add_argument("--job-id", action="append", required=True)
    cancel = sub.add_parser("cancel")
    cancel.add_argument("job_id")
    version = sub.add_parser("version")
    version.add_argument("task_id")
    version.add_argument("number", type=int)
    return top


async def run(args: argparse.Namespace) -> object:
    client = LocalControlFileClient(args.control_file)
    if args.command == "status":
        return await client.call("status", {})
    if args.command == "scale":
        return await client.call("scale", {"count": args.count})
    if args.command == "delegate":
        text = (args.text_file.read_text(encoding="utf-8")
                if args.text_file is not None else args.text)
        return await client.call("delegate", {
            "task_id": args.task_id, "task_version": args.task_version,
            "text": text, "instance_id": args.instance_id,
            "auto_expand": args.auto_expand,
        })
    if args.command == "wait":
        return await client.call("wait", {"job_ids": args.job_id})
    if args.command == "cancel":
        return await client.call("cancel", {"job_id": args.job_id})
    if args.command == "version":
        return await client.call("task_version", {
            "task_id": args.task_id, "version": args.number,
        })
    raise AssertionError(args.command)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    result = asyncio.run(run(args))
    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
