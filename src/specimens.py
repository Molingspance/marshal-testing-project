"""Representative marshal inputs built from stable case identifiers."""


_SAMPLE_CODE_SOURCE = """
def sample_function(number=3):
    text = "marshal"
    return f"{text}:{number + 1}"
"""


class _UnsupportedClass:
    def __init__(self):
        self.value = 1


def _sample_function(number=3):
    text = "marshal"
    return f"{text}:{number + 1}"


def _unsupported_function():
    return "functions themselves are not marshal values"


def _unsupported_generator():
    yield 1


def _build_sample_code_object():
    """Return a code object with a stable synthetic filename."""
    namespace = {}
    compiled = compile(_SAMPLE_CODE_SOURCE, "specimen_code.py", "exec")
    exec(compiled, namespace)  # noqa: S102 - controlled local source string.
    return namespace["sample_function"].__code__


SAMPLE_CODE_OBJECT = _build_sample_code_object()


VALID_CASE_IDS = (
    "none",
    "true",
    "false",
    "ellipsis",
    "stop_iteration",
    "int_zero",
    "int_one",
    "int_negative_one",
    "int_255",
    "int_256",
    "int_2_31_minus_1",
    "int_2_31",
    "int_2_63_minus_1",
    "int_2_63",
    "int_huge",
    "float_zero",
    "float_negative_zero",
    "float_one",
    "float_negative_one",
    "float_inf",
    "float_negative_inf",
    "float_nan",
    "complex_simple",
    "complex_with_nan",
    "string_empty",
    "string_ascii",
    "string_unicode",
    "string_emoji",
    "string_long",
    "bytes_empty",
    "bytes_null",
    "bytes_all_byte_values",
    "bytes_long",
    "list_empty",
    "list_single",
    "list_mixed",
    "list_nested",
    "list_large",
    "tuple_empty",
    "tuple_single",
    "tuple_nested",
    "tuple_large",
    "dict_empty",
    "dict_string_keys",
    "dict_int_keys",
    "dict_nested",
    "dict_different_insertion_order",
    "dict_large",
    "set_empty",
    "set_ints",
    "set_strings",
    "set_large_ints",
    "frozenset_empty",
    "frozenset_strings",
    "frozenset_large_ints",
    "recursive_list",
    "recursive_dict",
    "indirect_recursive_list",
    "shared_reference_list",
    "code_object_simple",
)


INVALID_CASE_IDS = (
    "unsupported_function",
    "unsupported_lambda",
    "unsupported_generator",
    "unsupported_instance",
    "unsupported_object",
    "unsupported_file_handle",
)


BOUNDARY_CASE_IDS = (
    "int_negative_one",
    "int_zero",
    "int_one",
    "int_255",
    "int_256",
    "int_2_31_minus_1",
    "int_2_31",
    "int_2_63_minus_1",
    "int_2_63",
    "int_huge",
    "float_zero",
    "float_negative_zero",
    "float_one",
    "float_negative_one",
    "float_inf",
    "float_negative_inf",
    "float_nan",
    "string_empty",
    "string_ascii",
    "string_unicode",
    "string_long",
    "bytes_empty",
    "bytes_null",
    "bytes_all_byte_values",
    "bytes_long",
    "list_empty",
    "list_single",
    "list_mixed",
    "list_nested",
    "list_large",
    "tuple_empty",
    "tuple_single",
    "tuple_nested",
    "tuple_large",
    "dict_empty",
    "dict_nested",
    "dict_large",
    "set_empty",
    "set_ints",
    "set_large_ints",
    "frozenset_large_ints",
)


DETERMINISM_CASE_IDS = (
    "none",
    "int_huge",
    "float_nan",
    "float_negative_zero",
    "string_unicode",
    "bytes_all_byte_values",
    "list_nested",
    "dict_string_keys",
    "dict_different_insertion_order",
    "set_ints",
    "set_strings",
    "frozenset_strings",
    "recursive_list",
    "recursive_dict",
    "shared_reference_list",
    "code_object_simple",
)


CROSS_PROCESS_CASE_IDS = (
    "none",
    "int_huge",
    "float_negative_zero",
    "float_nan",
    "string_unicode",
    "bytes_all_byte_values",
    "dict_string_keys",
    "dict_different_insertion_order",
    "set_ints",
    "set_strings",
    "frozenset_strings",
    "recursive_list",
    "recursive_dict",
    "shared_reference_list",
    "code_object_simple",
)


def build_specimen(case_id):
    """Build a fresh representative value for a case identifier."""
    if case_id == "none":
        return None
    if case_id == "true":
        return True
    if case_id == "false":
        return False
    if case_id == "ellipsis":
        return Ellipsis
    if case_id == "stop_iteration":
        return StopIteration
    if case_id == "int_zero":
        return 0
    if case_id == "int_one":
        return 1
    if case_id == "int_negative_one":
        return -1
    if case_id == "int_255":
        return 255
    if case_id == "int_256":
        return 256
    if case_id == "int_2_31_minus_1":
        return 2**31 - 1
    if case_id == "int_2_31":
        return 2**31
    if case_id == "int_2_63_minus_1":
        return 2**63 - 1
    if case_id == "int_2_63":
        return 2**63
    if case_id == "int_huge":
        return 2**4096 + 123456789
    if case_id == "float_zero":
        return 0.0
    if case_id == "float_negative_zero":
        return -0.0
    if case_id == "float_one":
        return 1.0
    if case_id == "float_negative_one":
        return -1.0
    if case_id == "float_inf":
        return float("inf")
    if case_id == "float_negative_inf":
        return float("-inf")
    if case_id == "float_nan":
        return float("nan")
    if case_id == "complex_simple":
        return complex(1.5, -2.25)
    if case_id == "complex_with_nan":
        return complex(float("nan"), -0.0)
    if case_id == "string_empty":
        return ""
    if case_id == "string_ascii":
        return "plain ascii text"
    if case_id == "string_unicode":
        return "unicode-\u6d4b\u8bd5-\u03c0"
    if case_id == "string_emoji":
        return "emoji-\U0001f600-\U0001f680"
    if case_id == "string_long":
        return "abc123-" * 1000
    if case_id == "bytes_empty":
        return b""
    if case_id == "bytes_null":
        return b"\x00inside\x00"
    if case_id == "bytes_all_byte_values":
        return bytes(range(256))
    if case_id == "bytes_long":
        return bytes([index % 251 for index in range(4096)])
    if case_id == "list_empty":
        return []
    if case_id == "list_single":
        return [1]
    if case_id == "list_mixed":
        return [None, True, 123, -0.0, "text", b"bytes"]
    if case_id == "list_nested":
        return [[1, 2], ["a", {"nested": (3, 4)}], []]
    if case_id == "list_large":
        return list(range(2048))
    if case_id == "tuple_empty":
        return ()
    if case_id == "tuple_single":
        return (1,)
    if case_id == "tuple_nested":
        return ((1, 2), ("a", "b"), (None, False))
    if case_id == "tuple_large":
        return tuple(range(2048))
    if case_id == "dict_empty":
        return {}
    if case_id == "dict_string_keys":
        return {"alpha": 1, "beta": [2, 3], "gamma": None}
    if case_id == "dict_int_keys":
        return {0: "zero", -1: "minus one", 2**31: "large"}
    if case_id == "dict_nested":
        return {"outer": {"inner": [1, 2, {"leaf": True}]}}
    if case_id == "dict_different_insertion_order":
        data = {}
        data["gamma"] = 3
        data["alpha"] = 1
        data["beta"] = 2
        return data
    if case_id == "dict_large":
        return {f"key-{index:04d}": index for index in range(1024)}
    if case_id == "set_empty":
        return set()
    if case_id == "set_ints":
        return {1, 2, 3, 255, 256}
    if case_id == "set_strings":
        return {"alpha", "beta", "gamma", "delta"}
    if case_id == "set_large_ints":
        return set(range(1024))
    if case_id == "frozenset_empty":
        return frozenset()
    if case_id == "frozenset_strings":
        return frozenset({"alpha", "beta", "gamma", "delta"})
    if case_id == "frozenset_large_ints":
        return frozenset(range(1024))
    if case_id == "recursive_list":
        value = []
        value.append(value)
        return value
    if case_id == "recursive_dict":
        value = {}
        value["self"] = value
        return value
    if case_id == "indirect_recursive_list":
        first = []
        second = [first]
        first.append(second)
        return first
    if case_id == "shared_reference_list":
        shared = ["shared"]
        return [shared, shared]
    if case_id == "code_object_simple":
        return SAMPLE_CODE_OBJECT
    if case_id == "unsupported_function":
        return _unsupported_function
    if case_id == "unsupported_lambda":
        return lambda value: value
    if case_id == "unsupported_generator":
        return _unsupported_generator()
    if case_id == "unsupported_instance":
        return _UnsupportedClass()
    if case_id == "unsupported_object":
        return object()
    if case_id == "unsupported_file_handle":
        return open(__file__, "rb")

    raise KeyError(f"unknown specimen case_id: {case_id}")


def all_valid_case_ids():
    return VALID_CASE_IDS


def all_invalid_case_ids():
    return INVALID_CASE_IDS


def all_boundary_case_ids():
    return BOUNDARY_CASE_IDS


def all_determinism_case_ids():
    return DETERMINISM_CASE_IDS


def all_cross_process_case_ids():
    return CROSS_PROCESS_CASE_IDS
