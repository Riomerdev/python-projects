from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from csv_sentinel.pipeline import PipelineError, run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Valida un CSV y separa filas incorrectas.")
    parser.add_argument("input", type=Path, help="CSV de entrada")
    parser.add_argument("--schema", required=True, type=Path, help="Esquema JSON")
    parser.add_argument("--output", required=True, type=Path, help="CSV limpio de salida")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        report = run_pipeline(args.input, args.schema, args.output)
    except (OSError, json.JSONDecodeError, PipelineError) as exc:
        print(f"csv-sentinel: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["rejected_rows"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
