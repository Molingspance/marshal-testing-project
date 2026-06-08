"""Run the marshal test suite with multiple Python versions.

The script looks for Python 3.9, 3.10, 3.11, 3.12, and 3.13 by default.
On Windows it prefers the Python launcher, for example ``py -3.11``. On
Linux and macOS it looks for commands such as ``python3.11``.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VERSIONS = ("3.9", "3.10", "3.11", "3.12", "3.13")


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
        default="results-multi",
        help="parent directory for per-version evidence",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return a failure status when any requested version is missing",
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
    commands: list[list[str]] = [[sys.executable]]
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

    return commands


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


def safe_label(system_name: str, version: str) -> str:
    return f"{system_name.lower()}-py{version.replace('.', '')}"


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def run_for_interpreter(info: dict, args: argparse.Namespace, output_root: Path) -> dict:
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
            "collect_results",
            info["command"]
            + [
                "tools/collect_results.py",
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


def main() -> int:
    args = parse_args()
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
