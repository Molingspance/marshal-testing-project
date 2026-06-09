# Commands

## Windows Python 3.10

```powershell
py -3.10 -m compileall src tools tests
py -3.10 -m unittest
py -3.10 tools\run_local.py --fuzz-count 2000 --results-dir results/results-windows-py310
```

## Linux Python 3.10

```bash
python3.10 -m compileall src tools tests
python3.10 -m unittest
python3.10 tools/run_local.py --fuzz-count 2000 --results-dir results/results-linux-py310
```

## macOS Python 3.10

```bash
python3.10 -m compileall src tools tests
python3.10 -m unittest
python3.10 tools/run_local.py --fuzz-count 2000 --results-dir results/results-macos-py310
```

## Windows Multi-Version Python

```powershell
python tools\run_compatibility.py --output-dir results/results-windows-multi
```

## Directory Layout

```text
marshal-testing-project/
  src/                         helper modules and test oracles
  tests/                       unittest test cases
  tools/                       result collection scripts
  results/                     all generated result outputs
    results-windows-py310/     Windows Python 3.10 result output
    results-linux-py310/       Linux Python 3.10 result output
    results-macos-py310/       macOS Python 3.10 result output
    results-windows-multi/     Windows multi-version Python result output
  report/                      final report
  README.md                    run commands and project layout
  requirements.txt             project dependency list
```
