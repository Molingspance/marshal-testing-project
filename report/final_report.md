# Testing the Stability and Correctness of Python's `marshal` Module

Repository: <https://github.com/Molingspance/marshal-testing-project>

## 1 Introduction

The `marshal` module is a foundational component of Python's standard library. It is mainly used for serialization and deserialization of selected internal object types. Serialization converts a Python object into a byte stream, while deserialization reconstructs the corresponding object structure from that byte stream. `marshal` is commonly involved in `.pyc` handling and related runtime scenarios, so although it is not intended for general-purpose data exchange like `json`, it remains an important part of the Python runtime ecosystem.

Even though the purpose of `marshal` is clear, developers still care about its stability and correctness in practice. In particular, under different execution environments, different Python versions, special floating-point values, recursive structures, and complex container objects, a central question naturally arises: for the same input object, does `marshal` always produce exactly the same output byte stream, and after deserialization, is the resulting object still equivalent to the original one?

The consistency of `marshal` output may be affected by several factors, such as:

- different operating systems
- different Python versions
- special floating-point values and sign handling
- recursive structures and shared references

Therefore, this project designs a test suite around the stability and correctness of `marshal`. The suite combines Black-Box Testing and White-Box Testing ideas, covering Equivalence Partitioning, Boundary Value Analysis, Fuzz Testing, source-guided structural analysis, and environment-difference testing. It systematically investigates the question of whether the same input always produces hash-identical output.

This report explains the test oracles, test design, Traceability Matrix, key findings, and limitations of the `marshal` test suite.

### 1.1 Test Oracles

Because the behavior of `marshal` cannot be judged by plain equality alone, the project defines multiple test oracles to support later analysis:

- Round-trip oracle: for a valid object `x`, `marshal.loads(marshal.dumps(x))` should reconstruct an object equivalent to `x`.
- Hash stability oracle: for the same object, repeated calls to `marshal.dumps(x)` should produce byte streams with identical SHA-256 hashes.
- Exception oracle: unsupported objects or corrupted byte streams should raise reasonable exceptions rather than crash the interpreter.
- Structural equivalence oracle: `NaN`, `-0.0`, recursive structures, shared references, and code objects are compared with custom equivalence logic instead of plain `==`.

## 2 Black-Box Testing

The goal of Black-Box Testing is to evaluate and verify the stability and correctness of the `marshal` module from the user's perspective. The tests do not depend on implementation details; instead, they focus on whether identical inputs produce identical outputs and whether deserialized objects remain correct. This helps expose potential defects and boundary issues through input design and output comparison.

To begin understanding how `marshal` behaves, the project first selects identical input objects and checks whether `marshal.dumps(obj)` consistently produces the same serialized output, especially across different data types and edge-case scenarios. To achieve this, the Black-Box Testing part mainly uses the following methods:

- Equivalence Partitioning
- Boundary Value Analysis
- Fuzz Testing

### 2.1 Equivalence Class Partitioning

By selecting representative object types, the project simulates the main kinds of inputs that `marshal` may handle in realistic usage and checks serialization stability across different object categories. This helps identify whether a specific type is more likely to trigger output inconsistency and also provides stable samples for later environment-difference testing.

The constructed equivalence classes mainly cover:

- basic atomic types: `None`, `bool`, `int`, `float`, `complex`, `str`, `bytes`
- compound container structures: `list`, `tuple`, `dict`, `set`, `frozenset`
- special structures: recursive lists, recursive dictionaries, indirect recursive structures, shared-reference structures
- special serializable objects: code objects
- unsupported object types: functions, lambda expressions, generators, normal class instances, file handles

This partitioning strategy is appropriate because different object types usually enter different marshal handling paths. Once the main equivalence classes are covered, the test suite can cover a large portion of the input space that users are most likely to encounter.

In this project, the representative specimens are constructed in `src/specimens.py` and exercised in `tests/test_roundtrip.py` and `tests/test_invalid_inputs.py`.

Representative test cases include:

- `none`: the most basic atomic class
- `dict_string_keys`: a typical dictionary class
- `recursive_list`: a recursive-structure class
- `code_object_simple`: a special serializable-object class
- `unsupported_function`: an unsupported-object class

Example test methods:

- `test_all_valid_specimens_roundtrip()`: performs round-trip checks over the main valid equivalence classes
- `test_file_api_roundtrip()`: checks the `dump/load` file API on representative equivalence classes
- `test_unsupported_objects_raise_reasonable_exceptions()`: validates exception paths for unsupported equivalence classes

### 2.2 Boundary Value Analysis

Since many problems tend to appear near extreme boundaries, the project designs specific test cases for numeric boundaries, special states, and edge structures that `marshal` may encounter. These tests directly verify stability and correctness under critical conditions.

The main boundary cases include:

- integer boundaries: `-1`, `0`, `1`, `255`, `256`, `2**31 - 1`, `2**31`, `2**63 - 1`, `2**63`, and a huge integer
- special floating-point values: `inf`, `-inf`, `NaN`, and `-0.0`
- empty objects: empty lists, empty dictionaries, empty strings, and empty bytes
- large-scale objects: long strings, large bytes, large lists, large tuples, and large dictionaries
- nested structures: multi-level nested lists and dictionaries

These boundary values were chosen because they are more likely to expose changes in encoding representation, loss of sign information, special handling of empty structures, and issues in processing large objects.

The corresponding tests are mainly implemented in:

- `tests/test_boundaries.py`

Representative boundary cases include:

- `int_255` / `int_256`
- `int_2_63_minus_1` / `int_2_63`
- `float_negative_zero`
- `float_nan`
- `bytes_all_byte_values`
- `list_large`

Example test methods:

- `test_boundary_cases_roundtrip()`: checks round-trip correctness for boundary-value objects
- `test_boundary_cases_stable_in_process()`: checks repeated-dumps stability for boundary-value objects

### 2.3 Fuzz Testing

Fuzz Testing automatically generates large amounts of complex and random input in order to test the stability and robustness of `marshal` under unconventional scenarios. Unlike Boundary Value Analysis and Equivalence Partitioning, which rely on predetermined values, Fuzz Testing explores a broader input space programmatically.

This project uses two forms of Fuzz Testing:

- Generation-based fuzzing: generate valid Python objects from a recursive grammar and verify round-trip correctness together with repeated-dumps stability
- Lexical fuzzing: mutate existing marshal byte streams by truncation, insertion, bit flips, type-tag replacement, and random suffixes in order to test the error-handling behavior of `marshal.loads()`

The generated fuzzing objects have the following characteristics:

- 2 to 4 levels of nested `list` / `tuple` / `dict` / `set` / `frozenset`
- mixed combinations of integers, strings, floats, `None`, booleans, and special floating-point values
- random-length strings and bytes
- controlled container sizes and recursion depth to balance complexity and execution cost

The local fuzzing results show that:

- with the fixed seed `20260607`, 1000 generation-based cases were executed and no round-trip or same-process stability failure was found
- lexical fuzzing produced 30 mutated byte streams, of which 21 raised controlled exceptions and 9 still decoded into valid objects

This suggests that `marshal` behaves stably for random valid objects within the current budget, but for corrupted byte streams, some mutations may accidentally form another valid marshal stream. In addition, `tests/test_invalid_inputs.py` contains targeted checks for unsupported objects and intentionally corrupted streams such as functions, lambda expressions, generators, file handles, empty byte streams, invalid type tags, and truncated objects, in order to verify that `marshal` enters the expected exception paths and raises reasonable exceptions.

Representative fuzzing input models include:

- valid random objects: 2 to 4 levels of nested `list` / `tuple` / `dict` / `set` / `frozenset`
- targeted corrupted inputs: empty byte streams, truncated streams, invalid type tags, and bit-flipped mutated streams

Example test methods:

- `test_generated_values_roundtrip_and_remain_stable()`: executes generation-based fuzzing
- `test_targeted_corrupted_streams_raise_reasonable_exceptions()`: checks exception paths for targeted corrupted streams
- `test_lexical_fuzzing_does_not_crash_process()`: executes lexical fuzzing and summarizes exception outcomes

## 3 White-Box Testing

White-Box Testing focuses on the internal structure and implementation paths of the program under test. In the strict form taught in structural testing, statement coverage, branch coverage, and condition coverage are measured from real executed source-code paths.

For Python's `marshal` module, exact C-level coverage would require rebuilding CPython with coverage instrumentation and then running the test suite with that specially built interpreter. This project does not rebuild or instrument CPython, so it does not report exact statement, branch, or condition coverage percentages for `Python/marshal.c`.

Instead, the project uses a source-guided representative-path approach. It reads the major type-dispatch and error-handling paths in `marshal.c`, maps them to concrete Python specimens, and validates the observed behavior through round-trip, stability, and exception checks. The only numeric coverage example in this project is for the helper function `_register_pair()` in `src/oracles.py`, which is part of the project's own comparison oracle.

### 3.1 Statement Coverage

Statement Coverage requires every executable statement to be executed at least once. Because this project does not instrument CPython, it does not claim exact statement coverage for `marshal.c`. For `marshal`, the practical objective is to exercise the main serialization and error-handling paths with representative inputs.

The project focuses on the following representative statements:

- singleton objects: `None`, `True`, `False`, `Ellipsis`, `StopIteration`
- numeric objects: `int`, `float`, `complex`
- text and binary objects: `str`, `bytes`
- container objects: `list`, `tuple`, `dict`, `set`, `frozenset`
- special cases: code objects, recursive structures, shared references, unsupported objects, and corrupted byte streams

Each class is exercised by at least one representative specimen and then checked by round-trip and stability tests.

For an explicit numeric example inside the project code, the project uses `_register_pair()` in `src/oracles.py`:

- test case 1: first visit of a new left/right object pair, `88.89%`
- test case 2: revisit of an already registered left/right object pair, `66.67%`
- combined statement coverage: `100.0%`

Together, these two tests cover all 9 executable statements in `_register_pair()`. This numeric result is a representative white-box example for project code, not a C-level coverage result for `marshal.c`.

The detailed mapping is recorded in:

- `results/source_checklist.md`
- `results/statement_coverage.md`

Example test methods:

- `tests/test_statement_coverage.py::test_register_pair_first_visit()`: covers the "first registration" path
- `tests/test_statement_coverage.py::test_register_pair_revisit()`: covers the "already registered revisit" path

### 3.2 Branch Coverage

Branch Coverage requires each important decision outcome to be executed at least once. The project does not measure exact branch coverage for `marshal.c`; instead, it exercises representative branch outcomes that are visible through the public `marshal` API:

- successful serialization / serialization exceptions
- successful loading / corrupted-stream exceptions
- normal containers / recursive or shared-reference containers
- normal floats / special `NaN` and `-0.0`

Representative tests:

- `tests/test_cycles.py`
- `tests/test_invalid_inputs.py`

Example test methods:

- `tests/test_cycles.py::test_recursive_list_roundtrip_preserves_cycle()`: covers the recursive-list branch
- `tests/test_cycles.py::test_recursive_dict_roundtrip_preserves_cycle()`: covers the recursive-dictionary branch
- `tests/test_invalid_inputs.py::test_unsupported_objects_raise_reasonable_exceptions()`: covers the unsupported-object exception branch
- `tests/test_invalid_inputs.py::test_targeted_corrupted_streams_raise_reasonable_exceptions()`: covers the corrupted-byte-stream exception branch

### 3.3 Condition Coverage

Condition Coverage focuses on whether each boolean condition is exercised with both True and False outcomes. The project does not measure exact condition coverage for `marshal.c`; instead, it triggers representative conditions that are important for byte-level serialization behavior.

The project emphasizes the following important conditions:

- whether a floating-point value is `NaN`
- whether a zero-valued float has a negative sign
- whether a container is empty
- whether a container contains recursive references
- whether an input byte stream is truncated
- whether the first type tag is invalid

These conditions are triggered by representative specimens such as:

- `float_nan`
- `float_negative_zero`
- `list_empty` / `dict_empty`
- `recursive_list` / `recursive_dict`
- `invalid-tag` / `truncated-list`

Therefore, the project's Condition Coverage is expressed as representative condition triggering and validation, rather than numeric coverage results from automated instrumentation.

Example test methods:

- `test_boundary_cases_roundtrip()`: covers key conditions involving `NaN`, `-0.0`, and empty containers
- `test_equivalent_handles_cycles_without_infinite_recursion()`: covers recursive-structure comparison conditions
- `test_targeted_corrupted_streams_raise_reasonable_exceptions()`: covers truncated-stream and invalid-tag conditions

## 4 Compatibility Testing

The compatibility testing plan covers the following environmental factors:

- Using the same `marshal` specimen set and test oracles, the same test cases should be run under different Python versions. The bundled local baseline uses Python 3.9.15, and the prepared Continuous Integration workflow covers Python 3.10, 3.11, 3.12, and 3.13. The comparison focuses on round-trip behavior and SHA-256 hashes of generated byte streams. Since `marshal` is an internal format and is not guaranteed to remain byte-stable across versions, version-level byte differences are treated as compatibility evidence rather than automatic defects.
- Running the same Python version and identical test cases on different operating systems (Windows, Linux, and macOS), the project observes whether serialization results differ. The comparison focuses on portability-related factors such as file paths, text encoding, and system-level behavior. The automated workflow is an implementation of the Continuous Integration / CI-CD idea discussed in the lectures: the same test suite is run repeatedly in controlled environments.

## 5 Traceability Matrix

| Test Objective / Requirement | Equivalence Class Example | Boundary Value Example | Fuzz Testing Example | Compatibility Testing Example |
| --- | --- | --- | --- | --- |
| Stability verification: identical input produces identical output | `dict_string_keys` | `int_256`, `float_negative_zero` | generated nested containers | Continuous Integration workflow |
| Correctness verification: objects remain equivalent after round-trip | `string_unicode`, `list_nested` | `float_nan`, `bytes_all_byte_values` | generated legal values | same-version repeated dumps |
| Basic type processing | `int_one`, `float_one`, `string_ascii` | `int_huge`, `float_inf` | random scalar generation | same OS / same version |
| Compound structure processing | `tuple_nested`, `dict_nested` | `list_large`, `dict_large` | nested random containers | different operating systems and Python versions |
| Special structure processing | `recursive_list`, `recursive_dict`, `shared_reference_list` | indirect recursion | generated nested recursion-free structures | different operating systems and Python versions |
| Extreme value processing | representative integer / float classes | `2**63`, `NaN`, `-0.0` | random large-range numbers | different Python versions |
| Empty structure processing | `list_empty`, `dict_empty`, `bytes_empty` | empty values | random empty containers | same OS repeated runs |
| Deep nesting processing | `list_nested`, `dict_nested` | large nested cases | recursive grammar generation | Continuous Integration workflow runs |
| Invalid input handling | unsupported function / file handle | truncated stream | mutated byte streams | Continuous Integration workflow runs |
| Statement Coverage example | `_register_pair()` first visit | `_register_pair()` revisit | not applicable | `results/statement_coverage.md` |

## 6 Key Findings

Through Black-Box Testing and White-Box Testing, the project identified the following key findings.

### 6.1 Round-Trip Correctness Holds for Representative Valid Inputs

Phenomenon: for the representative valid inputs covered by the project, including primitive types, nested containers, recursive structures, shared references, and code objects, `marshal.loads(marshal.dumps(x))` reconstructed structures equivalent to the originals.

Reason: the core goal of `marshal` is closer to object reconstruction than to cross-environment byte-level consistency. Within the current testing scope, it performs well in preserving object meaning after deserialization.

### 6.2 Corrupted Byte Streams Do Not Always Fail

Phenomenon: in lexical fuzzing, 9 out of 30 mutated byte streams were still successfully decoded instead of raising exceptions.

Reason: some corruption methods merely transformed the original byte stream into another still-valid marshal encoding, or appended trailing data after a complete object in a way that did not prevent parsing. Therefore, corrupted input should not always be assumed to fail.

## 7 Limitations and Recommendations

Although the project covers `marshal` behavior across a range of input types and environment factors, the following limitations and possible improvements remain:

1. The current evidence mainly comes from the local Windows + Python 3.9.15 environment; complete executed evidence across operating systems and Python versions has not yet been fully bundled.
2. Within White-Box Testing, only `_register_pair()` has an explicit Statement Coverage calculation; for the remaining `marshal.c`-related implementation paths, the project still relies on a source-guided representative-path approach rather than precise instrumented Statement Coverage, Branch Coverage, and Condition Coverage percentages.
3. The project does not perform mutation testing and does not report a mutation score.
4. Fuzzing increases confidence but cannot prove the absence of defects.
5. Extremely deep nesting, extremely large objects, and additional hardware platforms may still reveal compatibility issues not yet covered.

Based on the current test results, the project makes the following recommendations:

- If the goal is to reconstruct objects within the same environment, `marshal` is a reasonable choice.
- If the goal is strict byte-level consistency across platforms or Python versions, `marshal` is not an appropriate serialization format.
- If a use case requires stable and controllable cross-environment exchange, a more explicit protocol such as JSON, MessagePack, or a custom stable format should be preferred.

## 8 Conclusion

This project systematically evaluated the stability and correctness of Python's `marshal` module through Equivalence Partitioning, Boundary Value Analysis, Fuzz Testing, source-guided structural analysis, and environment-difference testing.

The test results show that:

- `marshal` has good round-trip correctness for the representative valid inputs covered by the suite
- within the same process, the output is usually stable
- compatibility testing across operating systems and Python versions is prepared through the Continuous Integration workflow
- `marshal` is better suited to preserving object reconstruction than to guaranteeing byte-level consistency across environments

In summary, `marshal` is suitable for object persistence and internal data handling within the same runtime ecosystem. However, if a scenario requires strict cross-platform or cross-version byte-level consistency, a more stable and controllable serialization scheme should be used instead.

## 9 AI Usage Disclosure

AI assistance was used during the organization and wording of this report, but the final content was manually reviewed, revised, and aligned with the actual test results.
