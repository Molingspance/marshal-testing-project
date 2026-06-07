"""Compute a concrete statement-coverage example for the white-box section."""

from __future__ import annotations

import ast
import inspect
import json
import sys
import textwrap
import trace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.oracles import _ComparisonState, _register_pair


def case_1_first_visit() -> None:
    left = []
    right = []
    state = _ComparisonState()
    _register_pair(left, right, state)


def case_2_revisit() -> None:
    left = []
    right = []
    state = _ComparisonState(
        left_to_right={id(left): id(right)},
        right_to_left={id(right): id(left)},
    )
    _register_pair(left, right, state)


def get_statement_lines() -> list[int]:
    source_lines, start_line = inspect.getsourcelines(_register_pair)
    module = ast.parse(textwrap.dedent("".join(source_lines)))
    function_def = module.body[0]
    statement_lines = sorted(
        {
            start_line + node.lineno - 1
            for node in ast.walk(function_def)
            if isinstance(node, ast.stmt) and not isinstance(node, ast.FunctionDef)
        }
    )
    return statement_lines


def run_case(case_function) -> set[int]:
    tracer = trace.Trace(count=True, trace=False)
    tracer.runfunc(case_function)
    counts = tracer.results().counts
    target_file = str(Path(inspect.getsourcefile(_register_pair)).resolve())
    return {
        lineno
        for (filename, lineno), count in counts.items()
        if Path(filename).resolve() == Path(target_file) and count > 0
    }


def coverage_percent(covered: set[int], total: list[int]) -> float:
    return round(100.0 * len(set(total) & covered) / len(total), 2)


def build_payload() -> dict:
    statement_lines = get_statement_lines()
    case_1_lines = run_case(case_1_first_visit)
    case_2_lines = run_case(case_2_revisit)
    combined = case_1_lines | case_2_lines

    return {
        "target_file": str(Path(inspect.getsourcefile(_register_pair)).resolve()),
        "target_function": "_register_pair",
        "statement_lines": statement_lines,
        "test_case_1": {
            "covered_lines": sorted(set(statement_lines) & case_1_lines),
            "coverage_percent": coverage_percent(case_1_lines, statement_lines),
            "description": "first visit of a new left/right object pair",
        },
        "test_case_2": {
            "covered_lines": sorted(set(statement_lines) & case_2_lines),
            "coverage_percent": coverage_percent(case_2_lines, statement_lines),
            "description": "revisit of an already registered left/right object pair",
        },
        "combined": {
            "covered_lines": sorted(set(statement_lines) & combined),
            "coverage_percent": coverage_percent(combined, statement_lines),
        },
    }


def write_results(payload: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "statement_coverage.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    markdown = f"""# Statement Coverage Example

Target function:

- `src/oracles.py::_register_pair`

Statement lines:

- `{payload["statement_lines"]}`

Test case 1:

- description: {payload["test_case_1"]["description"]}
- covered lines: `{payload["test_case_1"]["covered_lines"]}`
- statement coverage: `{payload["test_case_1"]["coverage_percent"]}%`

Test case 2:

- description: {payload["test_case_2"]["description"]}
- covered lines: `{payload["test_case_2"]["covered_lines"]}`
- statement coverage: `{payload["test_case_2"]["coverage_percent"]}%`

Combined result:

- covered lines: `{payload["combined"]["covered_lines"]}`
- statement coverage: `{payload["combined"]["coverage_percent"]}%`

Interpretation:

- Test case 1 exercises the path where a left/right object pair is seen for the first time.
- Test case 2 exercises the path where the same pair has already been registered.
- Together, the two test cases cover all executable statements in `_register_pair`, giving 100% statement coverage for this representative white-box target.
"""
    (RESULTS_DIR / "statement_coverage.md").write_text(markdown, encoding="utf-8")


def main() -> int:
    payload = build_payload()
    write_results(payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
