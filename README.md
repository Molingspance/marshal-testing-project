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

## Cross-Environment Result Comparison

After collecting the Windows, Linux, and macOS result directories, return to any
one environment and compare the result directories:

```bash
python tools/run_compatibility.py --compare-result-dirs results/results-windows-multi/py310 results/results-linux-py310 results/results-macos-py310
```

## Windows Multi-Version Python

If you manage Python versions with conda, create environments named with the
target version numbers. The compatibility runner will automatically try these
conda environments first:

```powershell
conda create -n 3.6 python=3.6
conda create -n 3.7 python=3.7
conda create -n 3.8 python=3.8
conda create -n 3.9 python=3.9
conda create -n 3.10 python=3.10
conda create -n 3.11 python=3.11
conda create -n 3.12 python=3.12
conda create -n 3.13 python=3.13
```
windows
```powershell
python tools\run_compatibility.py --output-dir results/results-windows-multi
```
linux
```powershell
python tools\run_compatibility.py --output-dir results/results-linux-multi
```
macos
```powershell
python tools\run_compatibility.py --output-dir results/results-macos-multi
```

To run only selected conda-backed versions:
```powershell
python tools\run_compatibility.py --versions 3.9 3.10 3.11
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
      py310/                   Python 3.10 evidence from that OS run
  report/                      final report
  README.md                    run commands and project layout
  requirements.txt             project dependency list
```
