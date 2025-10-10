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
from typing import Any

REQUIRED_TOP_LEVEL = {"input", "output"}
REQUIRED_INPUT_FIELDS = {
    "instruction",
    "mandatory_objects",
    "source_protocol_steps",
    "expected_final_states",
    "references",
}


def _fail(source: Path, message: str) -> ValueError:
    return ValueError(f"{source}: {message}")


def validate_sample(sample: dict[str, Any], source: Path) -> None:
    if not isinstance(sample, dict):
        raise _fail(source, "Top-level JSON value must be an object.")

    missing_top = REQUIRED_TOP_LEVEL - sample.keys()
    if missing_top:
        raise _fail(
            source, f"Missing required top-level keys: {sorted(missing_top)}."
        )

    input_section = sample["input"]
    if not isinstance(input_section, dict):
        raise _fail(source, "`input` must be an object.")

    missing_input = REQUIRED_INPUT_FIELDS - input_section.keys()
    if missing_input:
        raise _fail(
            source, f"Missing required input fields: {sorted(missing_input)}."
        )

    output_section = sample["output"]
    if not isinstance(output_section, dict):
        raise _fail(source, "`output` must be an object.")
    if "procedure_steps" not in output_section:
        raise _fail(source, "Missing required key `output.procedure_steps`.")


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
                try:
                    obj = json.load(f)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Failed to parse JSON file {fp}: {exc}"
                    ) from exc
            validate_sample(obj, fp)
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
