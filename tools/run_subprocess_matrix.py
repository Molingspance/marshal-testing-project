"""Compare marshal output across subprocesses and PYTHONHASHSEED values."""

from __future__ import annotations

import argparse
import json
import marshal
import os
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.oracles import sha256_bytes
from src.specimens import all_cross_process_case_ids, build_specimen


DEFAULT_SEEDS = ("0", "1", "42", "random")


def build_child_result(case_id: str) -> dict:
    """Serialize one specimen and return a JSON-friendly record."""
    result = {
        "case_id": case_id,
        "hash_seed": os.environ.get("PYTHONHASHSEED", "random"),
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
    }
    try:
        dumped = marshal.dumps(build_specimen(case_id))
    except Exception as exc:  # pragma: no cover - exercised via parent process.
        result["exception"] = {
            "message": str(exc),
            "type": type(exc).__name__,
        }
        result["hex_prefix"] = None
        result["length"] = None
        result["sha256"] = None
        return result

    result["exception"] = None
    result["hex_prefix"] = dumped[:16].hex()
    result["length"] = len(dumped)
    result["sha256"] = sha256_bytes(dumped)
    return result


def run_child(case_id: str) -> int:
    print(json.dumps(build_child_result(case_id), sort_keys=True))
    return 0


def run_case(case_id: str, seed: str) -> dict:
    """Run one case in a fresh subprocess with the requested hash seed."""
    env = os.environ.copy()
    if seed == "random":
        env.pop("PYTHONHASHSEED", None)
    else:
        env["PYTHONHASHSEED"] = seed

    command = [sys.executable, str(Path(__file__).resolve()), "--child", "--case", case_id]
    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        cwd=str(ROOT),
        env=env,
        text=True,
    )
    stdout = completed.stdout.strip()
    if completed.returncode != 0:
        raise RuntimeError(
            f"child process failed for case {case_id!r}, seed {seed!r}: "
            f"returncode={completed.returncode}, stderr={completed.stderr.strip()}"
        )
    if not stdout:
        raise RuntimeError(f"child process produced no JSON output for {case_id!r}")
    return json.loads(stdout)


def build_summary(records: list[dict]) -> dict:
    """Summarize per-case stability across subprocesses."""
    summary = {}
    for case_id in sorted({record["case_id"] for record in records}):
        group = [record for record in records if record["case_id"] == case_id]
        hashes = sorted({record["sha256"] for record in group if record["sha256"]})
        lengths = sorted({record["length"] for record in group if record["length"] is not None})
        exception_types = sorted(
            {
                record["exception"]["type"]
                for record in group
                if record["exception"] is not None
            }
        )
        summary[case_id] = {
            "exception_types": exception_types,
            "stable_across_seeds": len(hashes) <= 1 and not exception_types,
            "unique_hash_count": len(hashes),
            "unique_hashes": hashes,
            "unique_lengths": lengths,
        }
    return summary


def run_matrix(case_ids: list[str], seeds: list[str]) -> dict:
    """Execute the full subprocess matrix and return detailed evidence."""
    records = []
    for case_id in case_ids:
        for seed in seeds:
            records.append(run_case(case_id, seed))

    return {
        "case_ids": case_ids,
        "records": records,
        "seeds": seeds,
        "summary": build_summary(records),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="run the default case matrix")
    parser.add_argument("--case", help="run one case identifier")
    parser.add_argument(
        "--seed",
        action="append",
        help="add a hash seed to test; may be given multiple times",
    )
    parser.add_argument("--output", help="write parent-process JSON output to a file")
    parser.add_argument(
        "--child",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.child:
        if not args.case:
            raise SystemExit("--child requires --case")
        return run_child(args.case)

    if not args.all and not args.case:
        raise SystemExit("choose --all or --case")

    case_ids = [args.case] if args.case else list(all_cross_process_case_ids())
    seeds = args.seed or list(DEFAULT_SEEDS)
    payload = run_matrix(case_ids=case_ids, seeds=seeds)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
