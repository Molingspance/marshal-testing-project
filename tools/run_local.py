"""Run checks once in the current Python environment and write evidence."""

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
REQUIRED_SINGLE_VERSION = (3, 10)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.fuzz_generator import (
    DEFAULT_CASES,
    DEFAULT_SEED,
    run_generation_fuzz,
    summarize_lexical_fuzz,
)
from src.oracles import describe_value, sha256_bytes
from src.specimens import (
    all_valid_case_ids,
    boundary_value_samples,
    build_specimen,
    equivalence_class_samples,
    fuzzing_display_samples,
)


SET_ORDER_PROBE = {
    "marshal",
    "windows",
    "linux",
    "python",
    "hash",
    "stability",
    "boundary",
    "fuzzing",
}


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


def marshal_status(value: object) -> str:
    try:
        marshal.dumps(value)
    except Exception as exc:
        return f"unsupported: {type(exc).__name__}"
    return "supported"


def display_samples(
    title: str, samples: dict, unsupported_only: bool = False
) -> None:
    printed_title = False
    for name, value in samples.items():
        status = marshal_status(value)
        if unsupported_only and status == "supported":
            continue
        if not printed_title:
            print(f"[INFO] {title}")
            printed_title = True
        print(f"  - {name}: {describe_value(value)} [{status}]")


def report_hash_samples() -> dict:
    samples = {}
    # Include display samples in hash evidence so shown examples are recorded,
    # while the full unittest suite continues to use the case-id collections.
    for display_samples_dict in (
        equivalence_class_samples(),
        boundary_value_samples(),
        fuzzing_display_samples(),
    ):
        samples.update(display_samples_dict)

    for case_id in all_valid_case_ids():
        samples.setdefault(case_id, build_specimen(case_id))
    return samples


# Collect hashes for both display samples and the full valid case set.
def collect_marshal_hashes() -> dict:
    """Collect per-specimen marshal byte-stream hashes for comparison."""
    items = []
    for case_id, value in report_hash_samples().items():
        try:
            dumped = marshal.dumps(value)
        except Exception as exc:
            items.append(
                {
                    "case_id": case_id,
                    "description": describe_value(value),
                    "error": f"{type(exc).__name__}: {exc}",
                    "status": "error",
                }
            )
            continue

        items.append(
            {
                "case_id": case_id,
                "description": describe_value(value),
                "dump_length": len(dumped),
                "sha256": sha256_bytes(dumped),
                "status": "ok",
            }
        )

    return {
        "marshal_version": marshal.version,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "items": items,
    }


# Capture environment-sensitive values for OS comparison evidence.
def collect_environment_observations() -> dict:
    """Record platform details used by Windows/Linux comparison figures."""
    path_value = os.path.join("Users", "example", "\u8f6f\u4ef6\u6d4b\u8bd5")
    path_dump = marshal.dumps(path_value)
    set_dump = marshal.dumps(SET_ORDER_PROBE)
    return {
        "hash_seed": os.environ.get("PYTHONHASHSEED", "randomized-default"),
        "os_name": os.name,
        "path_altsep": os.altsep,
        "path_pathsep": os.pathsep,
        "path_sep": os.sep,
        "platform": platform.platform(),
        "path_probe": {
            "marshal_hex": path_dump.hex(),
            "original_object": path_value,
            "sha256": sha256_bytes(path_dump),
        },
        "python_version": platform.python_version(),
        "sample_joined_path": path_value,
        "set_order_probe": {
            "iteration_order": list(SET_ORDER_PROBE),
            "marshal_hex": set_dump.hex(),
            "repr": repr(SET_ORDER_PROBE),
            "sha256": sha256_bytes(set_dump),
            "sorted_values": sorted(SET_ORDER_PROBE),
        },
    }


# Print concise evidence sections while keeping supported cases out of stdout.
def print_report_figure_evidence(
    fuzzing_summary: dict, environment_observations: dict
) -> None:
    display_samples(
        "Unsupported equivalence-class samples",
        equivalence_class_samples(),
        unsupported_only=True,
    )
    display_samples(
        "Unsupported boundary-value samples",
        boundary_value_samples(),
        unsupported_only=True,
    )
    display_samples(
        "Unsupported fuzzing samples",
        fuzzing_display_samples(),
        unsupported_only=True,
    )

    lexical_summary = fuzzing_summary["lexical_summary"]
    print("[INFO] Lexical fuzzing result summary")
    print(
        "  - total={total}, loaded={loaded}, exceptions={exceptions}".format(
            total=lexical_summary["total"],
            loaded=lexical_summary["loaded"],
            exceptions=lexical_summary["exceptions"],
        )
    )

    path_probe = environment_observations["path_probe"]
    print("[INFO] System path separator evidence")
    print(f"  - path separator: {environment_observations['path_sep']!r}")
    print(f"  - original object: {path_probe['original_object']!r}")
    print(f"  - marshalled hex: {path_probe['marshal_hex']}")
    print(f"  - sha256 hash: {path_probe['sha256']}")

    set_probe = environment_observations["set_order_probe"]
    print("[INFO] Set ordering evidence")
    print(f"  - iteration order: {set_probe['iteration_order']}")
    print(f"  - repr: {set_probe['repr']}")
    print(f"  - sha256 hash: {set_probe['sha256']}")


# Run the local evidence collection workflow for one Python environment.
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
    unittest_output = unittest_result["stdout"]
    if unittest_result["stderr"]:
        unittest_output += "\n" + unittest_result["stderr"]
    write_text(results_dir / "unittest_output.txt", unittest_output)

    generation_failures = run_generation_fuzz(
        count=args.fuzz_count, seed=args.fuzz_seed
    )
    lexical_summary = summarize_lexical_fuzz(seed=args.fuzz_seed)
    fuzzing_summary = {
        "fuzz_count": args.fuzz_count,
        "fuzz_seed": args.fuzz_seed,
        "generation_failure_count": len(generation_failures),
        "generation_failures": generation_failures,
        "lexical_summary": lexical_summary,
    }
    write_json(results_dir / "fuzzing_summary.json", fuzzing_summary)
    environment_observations = collect_environment_observations()
    write_json(results_dir / "marshal_hashes.json", collect_marshal_hashes())
    write_json(
        results_dir / "environment_observations.json",
        environment_observations,
    )
    print_report_figure_evidence(fuzzing_summary, environment_observations)

    summary = {
        "evidence_files": [
            "unittest_output.txt",
            "fuzzing_summary.json",
            "marshal_hashes.json",
            "environment_observations.json",
        ],
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
