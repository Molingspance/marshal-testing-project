# marshal-testing-project

Test suite and report for evaluating the stability and correctness of Python's
`marshal` module.

Public repository: <https://github.com/Molingspance/marshal-testing-project>

## Scope

The project checks two core concerns:

- correctness: whether `marshal.loads(marshal.dumps(x))` reconstructs an equivalent value
- stability: whether the same logical input produces hash-identical bytes within one process

The suite combines representative fixed specimens, boundary-value tests,
negative tests, recursive-structure tests, same-process stability checks,
generation-based fuzzing, and lexical fuzzing for corrupted byte streams.

## Project Layout

```text
marshal-testing-project/
  src/        helper modules, specimens, and oracles
  tests/      unittest-based test suite
  tools/      result collection and statement-coverage scripts
  results/    generated evidence and analysis notes
  report/     final report
```

## How To Run

Run the unit test suite:

```bash
python -m unittest
```

Run the local evidence collection:

```bash
python tools/collect_results.py
```

Run the concrete white-box statement-coverage example:

```bash
python tools/statement_coverage_demo.py
```

Increase the generation-fuzzing workload when needed:

```bash
python tools/collect_results.py --fuzz-count 5000
```

## Manual Compatibility Runs

Run the same commands on Windows, macOS, and Linux when collecting
cross-operating-system evidence. On macOS and Linux, use `python3` if `python`
does not point to Python 3:

```bash
python3 -c "import platform, sys; print(sys.version); print(platform.platform())"
python3 -m compileall src tools tests
python3 -m unittest
python3 tools/collect_results.py --fuzz-count 2000
```

The key summary is written to `results/local_run_summary.json`.

## Environment

- local baseline used for the bundled evidence: Python 3.9.15 on Windows
- Continuous Integration workflow: Windows, Linux, and macOS on Python 3.10-3.13
- dependencies: Python standard library only

## Main Evidence Files

- `results/fuzzing_summary.json`: generation-based and lexical fuzzing summary
- `results/statement_coverage.md`: statement-coverage calculation for two white-box test cases
- `results/source_checklist.md`: source-guided structural analysis checklist
- `results/exploratory_sessions.md`: exploratory testing notes
- `report/final_report.md`: concise final report aligned with the assignment

## AI Disclosure

Parts of the report outline and wording were drafted with AI assistance and then
manually reviewed and edited.
