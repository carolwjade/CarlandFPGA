"""Register the two local Feishu roles; run from a node's own Codex session."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fpga_mesh.feishu_registration import register_role


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", choices="ABC", required=True)
    parser.add_argument("--role", choices=("astra", "deepseek", "both"), default="both")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    output = args.output_dir or (
        Path.cwd() / ".local" / "deployment" / f"node-{args.node.lower()}" / "feishu"
    )
    roles = ("astra", "deepseek") if args.role == "both" else (args.role,)
    for role in roles:
        info = register_role(node=args.node, role=role, output_dir=output)
        print(json.dumps({"role": role, "app_id": info["app_id"],
                          "secret_file": info["secret_file"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
