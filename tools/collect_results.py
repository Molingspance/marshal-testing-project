"""Run the project checks and write evidence files into results/."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.fuzz_generator import DEFAULT_CASES, DEFAULT_SEED, run_generation_fuzz, summarize_lexical_fuzz


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fuzz-count", type=int, default=DEFAULT_CASES)
    parser.add_argument("--fuzz-seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def run_command(command: list[str]) -> dict:
    """Run a subprocess and capture its output for evidence."""
    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        cwd=str(ROOT),
        text=True,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stderr": completed.stderr,
        "stdout": completed.stdout,
    }


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    args = parse_args()
    results_dir = ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    unittest_result = run_command([sys.executable, "-m", "unittest"])
    write_text(
        results_dir / "unittest_output.txt",
        unittest_result["stdout"] + ("\n" + unittest_result["stderr"] if unittest_result["stderr"] else ""),
    )

    matrix_output = results_dir / "hashes.json"
    matrix_result = run_command(
        [
            sys.executable,
            str(ROOT / "tools" / "run_subprocess_matrix.py"),
            "--all",
            "--output",
            str(matrix_output),
        ]
    )
    write_text(
        results_dir / "subprocess_matrix_output.txt",
        matrix_result["stdout"] + ("\n" + matrix_result["stderr"] if matrix_result["stderr"] else ""),
    )

    generation_failures = run_generation_fuzz(count=args.fuzz_count, seed=args.fuzz_seed)
    lexical_summary = summarize_lexical_fuzz(seed=args.fuzz_seed)
    fuzzing_summary = {
        "fuzz_count": args.fuzz_count,
        "fuzz_seed": args.fuzz_seed,
        "generation_failure_count": len(generation_failures),
        "generation_failures": generation_failures,
        "lexical_summary": lexical_summary,
    }
    write_json(results_dir / "fuzzing_summary.json", fuzzing_summary)

    summary = {
        "fuzzing": {
            "generation_failure_count": len(generation_failures),
            "lexical_loaded_count": lexical_summary["loaded"],
            "lexical_total": lexical_summary["total"],
        },
        "subprocess_matrix_passed": matrix_result["returncode"] == 0,
        "unittest_passed": unittest_result["returncode"] == 0,
    }
    write_json(results_dir / "local_run_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))

    return 0 if summary["unittest_passed"] and summary["subprocess_matrix_passed"] and not generation_failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
