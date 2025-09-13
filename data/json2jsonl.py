#!/usr/bin/env python3
"""
Convert a directory of JSON files into a single JSONL file.

Usage:
  python3 data/json2jsonl.py \
    --samples_dir data/example/samples \
    --output_path data/example/example.jsonl

Both arguments are optional; defaults target the example paths above.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def merge_json_to_jsonl(samples_dir: Path, output_path: Path) -> int:
    if not samples_dir.is_dir():
        raise FileNotFoundError(f"Samples directory not found: {samples_dir}")

    files = sorted(samples_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files found in {samples_dir}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with output_path.open("w", encoding="utf-8") as out:
        for fp in files:
            with fp.open("r", encoding="utf-8") as f:
                obj = json.load(f)
            line = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
            out.write(line + "\n")
            count += 1

    return count


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    default_samples = root / "data" / "example" / "samples"
    default_output = root / "data" / "example" / "example.jsonl"

    p = argparse.ArgumentParser(description="Merge JSON files into JSONL")
    p.add_argument(
        "--samples_dir",
        type=Path,
        default=default_samples,
        help=f"Directory containing input JSON files (default: {default_samples})",
    )
    p.add_argument(
        "--output_path",
        type=Path,
        default=default_output,
        help=f"Path to write JSONL output (default: {default_output})",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    n = merge_json_to_jsonl(args.samples_dir, args.output_path)
    print(f"Wrote {n} lines to {args.output_path}")


if __name__ == "__main__":
    main()
