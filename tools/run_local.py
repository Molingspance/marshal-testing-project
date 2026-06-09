"""Run checks once in the current Python environment and write evidence."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SINGLE_VERSION = (3, 10)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.fuzz_generator import DEFAULT_CASES, DEFAULT_SEED, run_generation_fuzz, summarize_lexical_fuzz


def platform_slug(system_name: str | None = None) -> str:
    name = system_name or platform.system()
    return {
        "Windows": "windows",
        "Linux": "linux",
        "Darwin": "macos",
    }.get(name, (name or "unknown").lower())


def default_results_dir() -> str:
    version = f"py{REQUIRED_SINGLE_VERSION[0]}{REQUIRED_SINGLE_VERSION[1]}"
    return f"results/results-{platform_slug()}-{version}"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fuzz-count", type=int, default=DEFAULT_CASES)
    parser.add_argument("--fuzz-seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--results-dir",
        default=None,
        help=(
            "directory where evidence files are written; when running Python 3.10, "
            "defaults to results/results-<os>-py310, for example "
            "results/results-windows-py310"
        ),
    )
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
    if args.results_dir is None and sys.version_info[:2] != REQUIRED_SINGLE_VERSION:
        expected = ".".join(str(part) for part in REQUIRED_SINGLE_VERSION)
        actual = f"{sys.version_info.major}.{sys.version_info.minor}"
        print(
            f"error: default result output is reserved for Python {expected}; "
            f"current interpreter is Python {actual}. Pass --results-dir explicitly.",
            file=sys.stderr,
        )
        return 2

    results_dir = Path(args.results_dir or default_results_dir())
    if not results_dir.is_absolute():
        results_dir = ROOT / results_dir
    results_dir.mkdir(parents=True, exist_ok=True)

    unittest_result = run_command([sys.executable, "-m", "unittest"])
    write_text(
        results_dir / "unittest_output.txt",
        unittest_result["stdout"] + ("\n" + unittest_result["stderr"] if unittest_result["stderr"] else ""),
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
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "results_dir": display_path(results_dir),
        "unittest_passed": unittest_result["returncode"] == 0,
    }
    write_json(results_dir / "local_run_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))

    return (
        0
        if summary["unittest_passed"]
        and not generation_failures
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
