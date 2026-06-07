# Testing the Stability and Correctness of Python's `marshal` Module

Repository: <https://github.com/Molingspance/marshal-testing-project>

## 1. Introduction and Scope

`marshal` serializes selected Python internal object types into a binary byte
stream and deserializes them back. This project tests two assignment goals:

- correctness: `marshal.loads(marshal.dumps(x))` should reconstruct a value equivalent to `x`
- stability: repeated serialization of the same input should produce hash-identical bytes

The system under test is the public API `marshal.dumps()`, `marshal.loads()`,
`marshal.dump()`, and `marshal.load()`.

## 2. Test Oracles

The suite uses several oracles because plain equality is not sufficient.

- Round-trip oracle: `loads(dumps(x))` must be equivalent to `x`.
- Hash stability oracle: repeated `dumps(x)` results must have the same SHA-256 digest.
- Exception oracle: unsupported objects and corrupted byte streams must raise controlled Python exceptions.
- Structural equivalence oracle: recursive containers, shared references, `NaN`, and signed zero are compared with custom logic in `src/oracles.py`.

## 3. Test Design

The suite combines course techniques as follows:

- Equivalence partitioning: scalar values, container values, recursive values, code objects, and unsupported values are split into explicit specimen classes in `src/specimens.py`.
- Boundary value analysis: integer width transitions (`255`, `256`, `2**31`, `2**63`), special floats, empty containers, and large strings/bytes/collections are tested in `tests/test_boundaries.py`.
- Property-based testing: the central property is `loads(dumps(x)) ~= x`.
- Generation-based fuzzing: `src/fuzz_generator.py` builds legal recursive marshal inputs from a small grammar.
- Lexical fuzzing: mutated marshal byte streams exercise error-handling paths in `tests/test_invalid_inputs.py`.
- Model-based testing: the generator uses a recursive value grammar as a lightweight model of valid marshalable inputs.
- Exploratory testing: three short sessions guided the design of the cross-process, corrupted-input, and floating-point tests.
- White-box supplement: a source-guided checklist maps the main `marshal.c` style paths to representative tests.

## 4. Why Specific Techniques Were Used or Not Used

- Equivalence partitioning was used because `marshal` behavior is strongly type-dependent.
- Boundary value analysis was used because serialization code often changes behavior at representation boundaries and empty/large container sizes.
- Generation-based fuzzing was used because the input domain is structured Python data, not plain text.
- Lexical fuzzing was used because `marshal.loads()` consumes raw bytes and must reject malformed streams safely.
- Property-based thinking was used because round-trip behavior is a natural invariant of serializers.
- Model-based testing was used in lightweight form through the recursive grammar used by the generator.
- Full white-box coverage was not used because rebuilding instrumented CPython is outside the project scope.
- Mocks were not emphasized because `marshal` does not depend on external services or slow collaborators.
- TDD was not a central technique because the assignment focuses on test design for an existing library, not on developing a new feature incrementally.
- AI testing was not used as a main technique because `marshal` is not an ML system, although the lecture's oracle discussion was still useful.

## 5. Traceability Matrix

| Requirement / concern | Technique | Main evidence | Oracle |
| --- | --- | --- | --- |
| Same input should produce hash-identical bytes | Same-process determinism + subprocess differential testing | `tests/test_determinism.py`, `tools/run_subprocess_matrix.py`, `results/hashes.json` | SHA-256 equality |
| Round-trip correctness | Example-based + property-based testing | `tests/test_roundtrip.py`, `tests/test_cycles.py` | structural equivalence |
| Float corner cases | Boundary value analysis | `tests/test_boundaries.py` | custom float oracle |
| Empty and large collections | Boundary value analysis | `tests/test_boundaries.py` | round-trip + stability |
| Recursive/cyclic structures | Structural testing | `tests/test_cycles.py` | alias/cycle preservation |
| Unsupported objects | Negative testing | `tests/test_invalid_inputs.py` | reasonable exception oracle |
| Corrupted byte streams | Lexical fuzzing + robustness testing | `tests/test_invalid_inputs.py`, `results/fuzzing_summary.json` | controlled exception |
| Random valid inputs | Generation-based fuzzing | `tests/test_fuzzing.py`, `results/fuzzing_summary.json` | round-trip + stability |
| Source-level dispatch coverage | Source-guided checklist | `results/source_checklist.md` | representative path coverage |

## 6. Findings

Bundled local evidence was collected on Python 3.9.15 on Windows.

- The unit suite passed locally.
- The round-trip property held for the representative valid specimens, including recursive containers and shared references.
- Repeated `marshal.dumps()` calls inside one process were stable for the tested valid specimens.
- Cross-process stability was not universal: string-based `set` and `frozenset` specimens changed hash across different `PYTHONHASHSEED` values, which is consistent with unordered container iteration depending on randomized string hashes.
- Ordered containers and the fixed-filename code-object specimen were stable across the tested subprocesses.
- Corrupted streams raised controlled Python exceptions during local testing; no interpreter crash was observed.
- In lexical fuzzing, 21 of 30 mutated streams raised controlled exceptions while 9 still decoded into valid objects because the mutation accidentally produced another legal marshal stream or appended trailing bytes after a complete value.
- The configured generation-based fuzzing run did not find a local counterexample.

These findings suggest that `marshal` is locally robust for the tested valid inputs, but byte-level stability depends on the concrete object shape and cannot be assumed for all unordered containers.

## 7. Limitations

- The project does not provide full C-level coverage or mutation score for CPython's implementation.
- Cross-version differences are expected to exist because the marshal format is intentionally not stable across Python versions.
- Fuzzing increases confidence but cannot prove the absence of bugs.
- Extremely large or adversarial objects were bounded to keep the suite reproducible and fast enough for CI.
- The bundled result files were generated locally on one machine; the CI workflow is intended to extend this evidence across operating systems and Python versions.

## 8. Reproducibility

Main commands:

```bash
python -m unittest
python tools/run_subprocess_matrix.py --all --output results/hashes.json
python tools/collect_results.py --fuzz-count 1000
```

The project uses only the Python standard library. CI is configured in
`.github/workflows/tests.yml` for Windows, Linux, and macOS on Python 3.10-3.13.

AI assistance note: parts of the report outline and wording were drafted with
AI assistance and then manually reviewed and edited.
