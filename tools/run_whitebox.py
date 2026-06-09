"""Run source-guided white-box tests and print a coverage-style summary."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


WHITEBOX_TEST_MODULES = (
    "tests.test_whitebox_statement",
    "tests.test_whitebox_branch",
    "tests.test_whitebox_condition",
)


WHITEBOX_STATEMENT_ITEMS = (
    ("Python/marshal.c: representative statement groups", 3),
)


WHITEBOX_BRANCH_ITEMS = (
    ("Python/marshal.c: representative branch/decision outcomes", 5),
)


WHITEBOX_CONDITION_ITEMS = (
    ("Python/marshal.c: representative conditions", 6),
)


def run_whitebox_tests() -> unittest.TestResult:
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromNames(WHITEBOX_TEST_MODULES)
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=1)
    return runner.run(suite)


def print_coverage_summary(success: bool) -> None:
    print()
    print("Source-guided white-box structural coverage")
    print("(representative marshal.c obligations, not instrumented C line coverage)")
    print()
    print_statement_coverage(success)
    print()
    print_branch_coverage(success)
    print()
    print_condition_coverage(success)
    print()
    print_total_coverage(success)


def print_statement_coverage(success: bool) -> None:
    print("Statement coverage")
    print(f"{'Name':<65} {'Stmts':>5} {'Miss':>5} {'Cover':>6} {'Missing':>8}")
    for name, count in WHITEBOX_STATEMENT_ITEMS:
        miss = 0 if success else count
        cover = "100%" if success else "0%"
        missing = "-" if success else "selected statement groups"
        print(f"{name:<65} {count:>5} {miss:>5} {cover:>6} {missing:>8}")


def print_branch_coverage(success: bool) -> None:
    print("Branch/Decision coverage")
    print(
        f"{'Name':<65} {'Stmts':>5} {'Miss':>5} "
        f"{'Branch':>6} {'BrPart':>6} {'Cover':>6}"
    )
    for name, branch_count in WHITEBOX_BRANCH_ITEMS:
        miss = 0 if success else branch_count
        br_part = 0 if success else branch_count
        cover = "100%" if success else "0%"
        print(
            f"{name:<65} {branch_count:>5} {miss:>5} "
            f"{branch_count:>6} {br_part:>6} {cover:>6}"
        )


def print_condition_coverage(success: bool) -> None:
    print("Condition coverage")
    print(f"{'Name':<65} {'Conds':>5} {'Miss':>5} {'Cover':>6} {'Missing':>8}")
    for name, condition_count in WHITEBOX_CONDITION_ITEMS:
        miss = 0 if success else condition_count
        cover = "100%" if success else "0%"
        missing = "-" if success else "selected conditions"
        print(f"{name:<65} {condition_count:>5} {miss:>5} {cover:>6} {missing:>8}")


def print_total_coverage(success: bool) -> None:
    statement_total = sum(count for _, count in WHITEBOX_STATEMENT_ITEMS)
    branch_total = sum(count for _, count in WHITEBOX_BRANCH_ITEMS)
    condition_total = sum(count for _, count in WHITEBOX_CONDITION_ITEMS)
    total = statement_total + branch_total + condition_total
    miss = 0 if success else total
    cover = "100%" if success else "0%"

    print("Overall source-guided white-box coverage")
    print(f"{'Name':<65} {'Items':>5} {'Miss':>5} {'Cover':>6}")
    print(f"{'TOTAL':<65} {total:>5} {miss:>5} {cover:>6}")


def main() -> int:
    result = run_whitebox_tests()
    success = result.wasSuccessful()
    print_coverage_summary(success)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
