# Source-Guided Structural Checklist

The project does not attempt full C-level `all-definitions` or `all-uses`
coverage for `Python/marshal.c`. That would require rebuilding and
instrumenting CPython. Instead, the suite uses a source-guided checklist to
ensure that the main marshal type-dispatch paths and error paths have at least
one representative test.

| marshal concern / path | Representative cases | Evidence |
| --- | --- | --- |
| `None`, booleans, sentinels | `none`, `true`, `false`, `ellipsis`, `stop_iteration` | `tests/test_roundtrip.py` |
| integer width transitions | `int_255`, `int_256`, `int_2_31`, `int_2_63`, `int_huge` | `tests/test_boundaries.py` |
| floats and special values | `float_negative_zero`, `float_inf`, `float_nan`, `complex_with_nan` | `tests/test_boundaries.py`, `tests/test_roundtrip.py` |
| strings and bytes | `string_unicode`, `string_long`, `bytes_null`, `bytes_all_byte_values`, `bytes_long` | `tests/test_boundaries.py` |
| sequential containers | `list_nested`, `list_large`, `tuple_nested`, `tuple_large` | `tests/test_boundaries.py`, `tests/test_roundtrip.py` |
| mappings | `dict_nested`, `dict_large`, `dict_different_insertion_order` | `tests/test_boundaries.py`, `tests/test_roundtrip.py` |
| sets and frozensets | `set_empty`, `set_ints`, `set_large_ints`, `frozenset_empty`, `frozenset_large_ints` | `tests/test_boundaries.py`, `tests/test_roundtrip.py` |
| recursive reference handling | `recursive_list`, `recursive_dict`, `indirect_recursive_list`, `shared_reference_list` | `tests/test_cycles.py`, `tests/test_roundtrip.py` |
| code object support | `code_object_simple` | `tests/test_roundtrip.py` |
| unsupported object rejection | `unsupported_function`, `unsupported_instance`, `unsupported_file_handle` | `tests/test_invalid_inputs.py` |
| invalid type tags / truncated input | `b""`, `b"\xff"`, truncated streams, mutated streams | `tests/test_invalid_inputs.py`, `src/fuzz_generator.py` |

This checklist is the white-box supplement used in the final report.
