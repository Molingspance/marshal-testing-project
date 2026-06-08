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
  results-windows/    generated Windows evidence
  results-rag-linux/  generated Linux server evidence
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

## Running Different Python Versions

The project provides a one-command script for collecting executed evidence under
Python 3.9, 3.10, 3.11, 3.12, and 3.13:

```bash
python tools/run_multi_python.py
```

This command tries to run the following Python versions by default:

```text
Python 3.9
Python 3.10
Python 3.11
Python 3.12
Python 3.13
```

For each available version, it automatically runs:

```text
compileall
unittest
collect_results.py
```

On Windows, the per-version evidence is saved separately, for example:

```text
results-multi/windows-py39/
results-multi/windows-py310/
results-multi/windows-py311/
results-multi/windows-py312/
results-multi/windows-py313/
```

The combined summary is written to:

```text
results-multi/summary.json
```

By default, the script searches for those Python versions, runs `compileall`,
`unittest`, and `tools/collect_results.py`, then writes separate evidence
folders under `results-multi/`. A version should only be described as tested
after the script reports that version as passed.

Use a smaller fuzzing workload for a quick smoke run:

```bash
python tools/run_multi_python.py --fuzz-count 100
```

Fail the command when any requested version is missing:

```bash
python tools/run_multi_python.py --strict
```

Run only selected versions:

```bash
python tools/run_multi_python.py --versions 3.10 3.11
```

The manual commands below are useful when debugging a specific Python version.

On Windows, first list installed Python versions:

```powershell
py -0p
```

Then run the same checks with a selected version, for example Python 3.10:

```powershell
py -3.10 -m compileall src tools tests
py -3.10 -m unittest
py -3.10 tools\collect_results.py --fuzz-count 2000 --results-dir results-windows-py310
```

Repeat with other installed versions as needed:

```powershell
py -3.11 -m unittest
py -3.11 tools\collect_results.py --fuzz-count 2000 --results-dir results-windows-py311

py -3.12 -m unittest
py -3.12 tools\collect_results.py --fuzz-count 2000 --results-dir results-windows-py312

py -3.13 -m unittest
py -3.13 tools\collect_results.py --fuzz-count 2000 --results-dir results-windows-py313
```

The `--results-dir` value keeps the evidence from each Python version separate.

On Linux or macOS, use the versioned interpreter name if it is installed:

```bash
python3.10 -m compileall src tools tests
python3.10 -m unittest
python3.10 tools/collect_results.py --fuzz-count 2000 --results-dir results-linux-py310

python3.11 -m unittest
python3.11 tools/collect_results.py --fuzz-count 2000 --results-dir results-linux-py311

python3.12 -m unittest
python3.12 tools/collect_results.py --fuzz-count 2000 --results-dir results-linux-py312

python3.13 -m unittest
python3.13 tools/collect_results.py --fuzz-count 2000 --results-dir results-linux-py313
```

If a command such as `python3.12` is not found, that Python version is not
installed in the current environment and cannot be counted as executed evidence.

The GitHub Actions workflow in `.github/workflows/tests.yml` is prepared to run
the same checks on Windows, Linux, and macOS with Python 3.10, 3.11, 3.12, and
3.13. To use it, push the repository to GitHub and download the uploaded
artifacts from the Actions run. Those artifacts are the evidence for the
versions that actually completed.

## Environment

- bundled Windows evidence: Python 3.9.15
- bundled Linux server evidence: Python 3.10.12
- prepared GitHub Actions workflow: Windows, Linux, and macOS on Python 3.10-3.13
- dependencies: Python standard library only

## Main Evidence Files

- `results-windows/fuzzing_summary.json`: Windows generation-based and lexical fuzzing summary
- `results-windows/statement_coverage.md`: Windows statement-coverage calculation for two white-box test cases
- `results-rag-linux/fuzzing_summary.json`: Linux generation-based and lexical fuzzing summary
- `results-rag-linux/statement_coverage.md`: Linux statement-coverage calculation for two white-box test cases
- `report/final_report.md`: concise final report aligned with the assignment

## AI Disclosure

Parts of the report outline and wording were drafted with AI assistance and then
manually reviewed and edited.
