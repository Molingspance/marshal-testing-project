# marshal-testing-project

Test suite and report for evaluating the stability and correctness of Python's
`marshal` module.

Public repository: <https://github.com/Molingspance/marshal-testing-project>

## Scope

The project checks two core concerns:

- correctness: whether `marshal.loads(marshal.dumps(x))` reconstructs an equivalent value
- stability: whether the same logical input produces hash-identical bytes within one process and across subprocesses

The suite combines representative fixed specimens, boundary-value tests,
negative tests, recursive-structure tests, same-process determinism checks,
cross-process `PYTHONHASHSEED` comparison, generation-based fuzzing, and
lexical fuzzing for corrupted byte streams.

## Project Layout

```text
marshal-testing-project/
  src/        helper modules, specimens, and oracles
  tests/      unittest-based test suite
  tools/      subprocess matrix runner and result collection scripts
  results/    generated evidence and analysis notes
  report/     final report
```

## How To Run

Run the unit test suite:

```bash
python -m unittest
```

Run the same-process and cross-process evidence collection:

```bash
python tools/collect_results.py
```

Run only the subprocess stability matrix:

```bash
python tools/run_subprocess_matrix.py --all --output results/hashes.json
```

Increase the generation-fuzzing workload when needed:

```bash
python tools/collect_results.py --fuzz-count 5000
```

## Environment

- local baseline used for the bundled evidence: Python 3.9.15 on Windows
- CI matrix: Windows, Linux, and macOS on Python 3.10-3.13
- dependencies: Python standard library only

## Main Evidence Files

- `results/hashes.json`: cross-process stability data for selected specimens
- `results/fuzzing_summary.json`: generation-based and lexical fuzzing summary
- `results/source_checklist.md`: source-guided structural coverage checklist
- `results/exploratory_sessions.md`: exploratory testing notes
- `report/final_report.md`: concise final report aligned with the assignment

## AI Disclosure

Parts of the report outline and wording were drafted with AI assistance and then
manually reviewed and edited.
