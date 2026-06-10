"""Run compatibility checks across multiple Python versions.

The script looks for Python 3.6 through 3.13 by default.
It first looks for conda environments whose names match the requested
versions, for example ``3.9`` and ``3.10``. On Windows it then falls back to
the Python launcher, for example ``py -3.11``. The default output directory is
platform-specific, for example ``results/results-windows-multi`` on Windows.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSIONS = ("3.7","3.8","3.9", "3.10", "3.11", "3.12", "3.13")


def platform_slug(system_name: str | None = None) -> str:
    name = system_name or platform.system()
    return {
        "Windows": "windows",
        "Linux": "linux",
        "Darwin": "macos",
    }.get(name, (name or "unknown").lower())


def default_output_dir() -> str:
    return f"results/results-{platform_slug()}-multi"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--versions",
        nargs="+",
        default=DEFAULT_VERSIONS,
        help="Python versions to test, for example: --versions 3.10 3.11",
    )
    parser.add_argument("--fuzz-count", type=int, default=2000)
    parser.add_argument("--fuzz-seed", type=int, default=20260607)
    parser.add_argument(
        "--output-dir",
        default=default_output_dir(),
        help=(
            "parent directory for per-version evidence; defaults to "
            "results/results-<os>-multi"
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return a failure status when any requested version is missing",
    )
    parser.add_argument(
        "--compare-result-dirs",
        nargs="+",
        default=None,
        help=(
            "compare existing run_local.py result directories instead of "
            "running interpreters, for example results/results-windows-py310 "
            "results/results-linux-py310"
        ),
    )
    return parser.parse_args()


def run_command(command: list[str], cwd: Path = ROOT) -> dict:
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError as exc:
        return {
            "command": command,
            "returncode": 127,
            "stdout": "",
            "stderr": f"{type(exc).__name__}: {exc}",
        }

    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def candidate_commands(version: str) -> list[list[str]]:
    commands: list[list[str]] = []
    commands.extend(conda_candidate_commands(version))
    commands.append([sys.executable])
    if os.name == "nt" and shutil.which("py"):
        commands.append(["py", f"-{version}"])
        for executable in py_launcher_executables().get(version, []):
            commands.append([executable])

    executable_names = ["python", f"python{version}"]
    if os.name == "nt":
        executable_names.append(f"python{version.replace('.', '')}")

    for name in executable_names:
        if shutil.which(name):
            commands.append([name])

    return unique_commands(commands)


def conda_candidate_commands(version: str) -> list[list[str]]:
    env_name = version
    prefixes: list[Path] = []

    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        active_prefix = Path(conda_prefix)
        if active_prefix.name == env_name:
            prefixes.append(active_prefix)
        if active_prefix.parent.name == "envs":
            prefixes.append(active_prefix.parent / env_name)

    home = Path.home()
    if os.name == "nt":
        conda_roots = [home / "Miniconda3", home / "Anaconda3"]
    else:
        conda_roots = [home / "miniconda3", home / "anaconda3"]

    for root in conda_roots:
        prefixes.append(root / "envs" / env_name)

    prefixes.extend(
        Path(path_text)
        for path_text in conda_env_paths_by_name().get(env_name, [])
    )

    commands: list[list[str]] = []
    for prefix in unique_paths(prefixes):
        executable = conda_python_executable(prefix)
        if executable.exists():
            commands.append([str(executable)])

    conda = conda_executable()
    if conda:
        commands.append([conda, "run", "-n", env_name, "python"])
    return commands


def conda_python_executable(prefix: Path) -> Path:
    if os.name == "nt":
        return prefix / "python.exe"
    return prefix / "bin" / "python"


def conda_executable() -> str | None:
    candidates = [os.environ.get("CONDA_EXE"), shutil.which("conda")]
    for candidate in candidates:
        if not candidate:
            continue
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    return None


@functools.cache
def conda_env_paths_by_name() -> dict[str, list[str]]:
    conda = conda_executable()
    if not conda:
        return {}

    result = run_command([conda, "env", "list", "--json"])
    if result["returncode"] != 0:
        return {}

    text = result["stdout"].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return {}

    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}

    versions: dict[str, list[str]] = {}
    for env_path_text in payload.get("envs", []):
        env_path = Path(env_path_text)
        versions.setdefault(env_path.name, []).append(str(env_path))
    return versions


def unique_commands(commands: list[list[str]]) -> list[list[str]]:
    seen: set[tuple[str, ...]] = set()
    unique: list[list[str]] = []
    for command in commands:
        key = tuple(command)
        if key in seen:
            continue
        seen.add(key)
        unique.append(command)
    return unique


def unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        key = str(path).lower() if os.name == "nt" else str(path)
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def py_launcher_executables() -> dict[str, list[str]]:
    if os.name != "nt" or not shutil.which("py"):
        return {}

    result = run_command(["py", "-0p"])
    if result["returncode"] != 0:
        return {}

    versions: dict[str, list[str]] = {}
    for line in result["stdout"].splitlines():
        version_match = re.search(r"3\.\d+", line)
        path_match = re.search(r"([A-Za-z]:\\.*python(?:\.exe)?)\s*$", line)
        if version_match is None or path_match is None:
            continue

        version = version_match.group(0)
        executable = path_match.group(1)
        versions.setdefault(version, []).append(executable)

    return versions


def probe_interpreter(command: list[str], expected_version: str) -> dict | None:
    code = (
        "import platform, sys; "
        "print(f'{sys.version_info.major}.{sys.version_info.minor}\\t"
        "{sys.executable}\\t{platform.platform()}')"
    )
    result = run_command(command + ["-c", code])
    if result["returncode"] != 0:
        return None

    output = result["stdout"].strip()
    fields = output.split("\t", 2)
    if len(fields) != 3:
        return None

    actual_version, executable, platform_text = fields
    if actual_version != expected_version:
        return None

    return {
        "command": command,
        "version": actual_version,
        "executable": executable,
        "platform": platform_text,
    }


def find_interpreter(version: str, seen_executables: set[str]) -> dict | None:
    for command in candidate_commands(version):
        info = probe_interpreter(command, version)
        if info is None:
            continue

        executable_key = str(Path(info["executable"]).resolve()).lower()
        if executable_key in seen_executables:
            continue

        seen_executables.add(executable_key)
        return info

    return None


def safe_label(_system_name: str, version: str) -> str:
    return f"py{version.replace('.', '')}"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def run_for_interpreter(
    info: dict, args: argparse.Namespace, output_root: Path
) -> dict:
    version = info["version"]
    system_name = platform.system() or "unknown"
    evidence_dir = output_root / safe_label(system_name, version)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    steps = [
        (
            "compileall",
            info["command"] + ["-m", "compileall", "src", "tools", "tests"],
        ),
        ("unittest", info["command"] + ["-m", "unittest"]),
        (
            "run_local",
            info["command"]
            + [
                "tools/run_local.py",
                "--fuzz-count",
                str(args.fuzz_count),
                "--fuzz-seed",
                str(args.fuzz_seed),
                "--results-dir",
                str(evidence_dir),
            ],
        ),
    ]

    record = {
        "status": "passed",
        "version": version,
        "executable": info["executable"],
        "platform": info["platform"],
        "evidence_dir": display_path(evidence_dir),
        "steps": [],
    }

    print(f"[INFO] Running Python {version}: {info['executable']}")
    for name, command in steps:
        print(f"[INFO]  - {name}")
        result = run_command(command)
        record["steps"].append(result)
        if result["returncode"] != 0:
            record["status"] = "failed"
            break

    (evidence_dir / "command_log.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record


def evidence_dir_from_record(record: dict) -> Path:
    evidence_dir = Path(record["evidence_dir"])
    if evidence_dir.is_absolute():
        return evidence_dir
    return ROOT / evidence_dir


def load_hash_items(record: dict) -> dict[str, dict]:
    path = evidence_dir_from_record(record) / "marshal_hashes.json"
    if not path.exists():
        return {}

    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["case_id"]: item
        for item in payload.get("items", [])
        if item.get("status") == "ok"
    }


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def result_dir_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return ROOT / path


def load_hash_payload_from_dir(result_dir: Path) -> dict:
    path = result_dir / "marshal_hashes.json"
    if not path.exists():
        return {}
    return read_json(path)


def load_environment_payload_from_dir(result_dir: Path) -> dict:
    path = result_dir / "environment_observations.json"
    if not path.exists():
        return {}
    return read_json(path)


def hash_items_by_case(payload: dict, status: str) -> dict[str, dict]:
    return {
        item["case_id"]: item
        for item in payload.get("items", [])
        if item.get("status") == status
    }


def result_dir_errors(result_dir: Path) -> list[str]:
    errors = []
    if not result_dir.exists():
        return ["directory does not exist"]
    if not result_dir.is_dir():
        errors.append("path is not a directory")
    if not (result_dir / "marshal_hashes.json").exists():
        errors.append("missing marshal_hashes.json")
    return errors


def environment_summary(payload: dict) -> str:
    if not payload:
        return "environment metadata unavailable"

    platform_text = payload.get("platform") or "unknown platform"
    python_version = payload.get("python_version")
    if python_version:
        return f"{platform_text}, Python {python_version}"
    return str(platform_text)


def platform_label(payload: dict, result_dir: Path) -> str:
    platform_text = str(payload.get("platform") or "")
    if platform_text.startswith("Windows"):
        return "Windows"
    if platform_text.startswith("Linux"):
        return "Linux"
    if platform_text.startswith("macOS") or platform_text.startswith("Darwin"):
        return "macOS"

    path_text = str(result_dir).lower()
    if "windows" in path_text:
        return "Windows"
    if "linux" in path_text:
        return "Linux"
    if "macos" in path_text or "darwin" in path_text:
        return "macOS"
    return display_path(result_dir)


# Compare existing result directories produced on different environments.
def summarize_result_dir_differences(result_dirs: list[str]) -> list[dict]:
    paths = [result_dir_path(path_text) for path_text in result_dirs]
    if len(paths) < 2:
        message = "At least two result directories are required."
        print(f"[ERROR] {message}")
        return [{"status": "error", "message": message}]

    invalid = []
    for path in paths:
        errors = result_dir_errors(path)
        if not errors:
            continue
        label = display_path(path)
        print(f"[ERROR] Invalid result directory {label}: {', '.join(errors)}")
        invalid.append(
            {"status": "error", "result_dir": label, "errors": errors}
        )

    if invalid:
        return invalid

    baseline = paths[0]
    baseline_hashes = load_hash_payload_from_dir(baseline)
    baseline_ok = hash_items_by_case(baseline_hashes, "ok")
    baseline_unsupported = set(hash_items_by_case(baseline_hashes, "error"))
    baseline_env = load_environment_payload_from_dir(baseline)
    baseline_name = platform_label(baseline_env, baseline)

    print("[INFO] Comparing existing marshal result directories.")
    if baseline_unsupported:
        print(
            f"[INFO] {baseline_name} baseline unsupported items: "
            + ", ".join(sorted(baseline_unsupported))
        )

    comparisons = []
    for compared in paths[1:]:
        compared_hashes = load_hash_payload_from_dir(compared)
        compared_ok = hash_items_by_case(compared_hashes, "ok")
        compared_unsupported = set(hash_items_by_case(compared_hashes, "error"))
        compared_env = load_environment_payload_from_dir(compared)

        baseline_ok_ids = set(baseline_ok)
        compared_ok_ids = set(compared_ok)
        missing_ok = sorted(baseline_ok_ids - compared_ok_ids)
        extra_ok = sorted(compared_ok_ids - baseline_ok_ids)
        common_ok = sorted(baseline_ok_ids & compared_ok_ids)

        hash_mismatches = []
        for case_id in common_ok:
            baseline_item = baseline_ok[case_id]
            compared_item = compared_ok.get(case_id)
            if compared_item["sha256"] != baseline_item["sha256"]:
                hash_mismatches.append(case_id)

        unsupported_delta = sorted(
            baseline_unsupported.symmetric_difference(compared_unsupported)
        )
        path_diff = environment_field_diff(
            baseline_env, compared_env, "path_sep"
        )
        set_order_diff = environment_field_diff(
            baseline_env, compared_env, "set_order_probe", "iteration_order"
        )

        label = display_path(compared)
        compared_name = platform_label(compared_env, compared)
        if hash_mismatches:
            print(
                f"[X] {compared_name} marshal hash mismatch: "
                + ", ".join(hash_mismatches)
            )
        elif missing_ok or extra_ok:
            details = []
            if missing_ok:
                details.append("missing: " + ", ".join(missing_ok))
            if extra_ok:
                details.append("extra: " + ", ".join(extra_ok))
            print(
                f"[X] {compared_name} hash case set diff: "
                + "; ".join(details)
            )
        elif not common_ok:
            print(
                f"[X] {compared_name} marshal hash comparison skipped: "
                "no common ok cases"
            )
        else:
            print(
                f"[OK] {compared_name} marshal hash match: "
                f"{len(common_ok)} common ok cases, 0 hash mismatches"
            )

        if unsupported_delta:
            print(
                f"[X] {compared_name} unsupported set diff: "
                + ", ".join(unsupported_delta)
            )
        else:
            print(
                f"[OK] {compared_name} unsupported set match: "
                f"{len(baseline_unsupported)} unsupported items, 0 deltas"
            )

        if set_order_diff:
            print(
                f"[DIFF] {compared_name} set order differs from "
                f"{baseline_name} baseline: {set_order_diff}"
            )
        else:
            print(f"[OK] {compared_name} set order matches {baseline_name} baseline")

        environment_diffs = []
        if set_order_diff:
            environment_diffs.append("set_order")

        comparisons.append(
            {
                "compared_dir": label,
                "compared_name": compared_name,
                "compared_environment": environment_summary(compared_env),
                "common_ok_count": len(common_ok),
                "hash_mismatches": hash_mismatches,
                "missing_ok_cases": missing_ok,
                "extra_ok_cases": extra_ok,
                "path_separator_diff": path_diff,
                "set_order_diff": set_order_diff,
                "environment_diffs": environment_diffs,
                "unsupported_delta": unsupported_delta,
            }
        )

    print("[SUMMARY] Cross-environment comparison:")
    print(
        f"[SUMMARY] {baseline_name} baseline: "
        f"ok_cases={len(baseline_ok)}, unsupported_items={len(baseline_unsupported)}"
    )
    for comparison in comparisons:
        env_diffs = comparison["environment_diffs"]
        env_text = ",".join(env_diffs) if env_diffs else "none"
        print(
            "[SUMMARY] {name}: common_ok={common_ok}, "
            "hash_mismatches={hash_mismatches}, missing_ok={missing_ok}, "
            "extra_ok={extra_ok}, unsupported_delta={unsupported_delta}, "
            "env_diffs={env_diffs}".format(
                name=comparison["compared_name"],
                common_ok=comparison["common_ok_count"],
                hash_mismatches=len(comparison["hash_mismatches"]),
                missing_ok=len(comparison["missing_ok_cases"]),
                extra_ok=len(comparison["extra_ok_cases"]),
                unsupported_delta=len(comparison["unsupported_delta"]),
                env_diffs=env_text,
            )
        )

    return comparisons


def environment_field_diff(
    left: dict, right: dict, *field_path: str
) -> dict | None:
    if not left or not right:
        return None

    left_value = nested_get(left, field_path)
    right_value = nested_get(right, field_path)
    if left_value == right_value:
        return None
    return {"baseline": left_value, "compared": right_value}


def nested_get(payload: dict, field_path: tuple[str, ...]) -> object:
    current: object = payload
    for field in field_path:
        if not isinstance(current, dict):
            return None
        current = current.get(field)
    return current


# Compare marshal hashes across Python versions from compatibility runs.
def summarize_hash_consistency(runs: list[dict]) -> list[dict]:
    passed_runs = [run for run in runs if run.get("status") == "passed"]
    if len(passed_runs) < 2:
        return []

    baseline = next(
        (run for run in passed_runs if run.get("version") == "3.9"),
        passed_runs[0],
    )
    baseline_items = load_hash_items(baseline)
    print("[INFO] Checking for cross-version marshal hash consistency.")
    print(
        "[INFO] Baseline Python {version}: {path}".format(
            version=baseline["version"],
            path=baseline["evidence_dir"],
        )
    )

    comparisons = []
    for run in passed_runs:
        if run is baseline:
            continue

        compared_items = load_hash_items(run)
        mismatches = []
        for case_id, baseline_item in baseline_items.items():
            compared_item = compared_items.get(case_id)
            if compared_item is None:
                continue
            if compared_item["sha256"] != baseline_item["sha256"]:
                mismatches.append(case_id)

        if mismatches:
            print(
                "[X] MISMATCH with Python {version}: {items}".format(
                    version=run["version"],
                    items=", ".join(mismatches),
                )
            )
        else:
            print(f"[OK] MATCH with Python {run['version']}")

        comparisons.append(
            {
                "baseline_version": baseline["version"],
                "compared_version": run["version"],
                "mismatch_count": len(mismatches),
                "mismatched_items": mismatches,
            }
        )

    print("[INFO] Cross-version marshal hash comparison complete.")
    return comparisons


# Dispatch either compatibility execution or result-directory comparison.
def main() -> int:
    args = parse_args()
    if args.compare_result_dirs:
        comparisons = summarize_result_dir_differences(args.compare_result_dirs)
        if any(comparison.get("status") == "error" for comparison in comparisons):
            return 1
        return 0

    output_root = Path(args.output_dir)
    if not output_root.is_absolute():
        output_root = ROOT / output_root
    output_root.mkdir(parents=True, exist_ok=True)

    seen_executables: set[str] = set()
    summary = {
        "requested_versions": list(args.versions),
        "fuzz_count": args.fuzz_count,
        "fuzz_seed": args.fuzz_seed,
        "runs": [],
    }

    for version in args.versions:
        info = find_interpreter(version, seen_executables)
        if info is None:
            print(f"[SKIP] Python {version} was not found")
            summary["runs"].append({"version": version, "status": "missing"})
            continue

        summary["runs"].append(run_for_interpreter(info, args, output_root))

    summary["hash_consistency"] = summarize_hash_consistency(summary["runs"])

    summary_path = output_root / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[INFO] Summary written to {display_path(summary_path)}")

    failed = [run for run in summary["runs"] if run["status"] == "failed"]
    missing = [run for run in summary["runs"] if run["status"] == "missing"]
    if failed or (args.strict and missing):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
