"""Representative marshal inputs built from stable case identifiers."""

import datetime
import decimal
import sys
import uuid
from collections import Counter, OrderedDict, defaultdict, namedtuple


_SAMPLE_CODE_SOURCE = """
def sample_function(number=3):
    text = "marshal"
    return f"{text}:{number + 1}"
"""


class _UnsupportedClass:
    def __init__(self):
        self.value = 1


_UnsupportedNamedTuple = namedtuple("_UnsupportedNamedTuple", "value")


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
    "int_regular",
    "int_zero",
    "int_one",
    "int_negative_one",
    "int_min_64",
    "int_255",
    "int_256",
    "int_2_31_minus_1",
    "int_2_31",
    "int_2_63_minus_1",
    "int_2_63",
    "int_huge",
    "int_negative_huge",
    "float_pi",
    "float_zero",
    "float_negative_zero",
    "float_one",
    "float_negative_one",
    "float_max_finite",
    "float_min_positive",
    "float_subnormal",
    "float_inf",
    "float_negative_inf",
    "float_nan",
    "complex_simple",
    "complex_with_nan",
    "string_empty",
    "string_ascii",
    "string_hello",
    "string_unicode",
    "string_chinese",
    "string_emoji",
    "string_long",
    "path_windows_like",
    "path_posix_like",
    "bytes_empty",
    "bytes_null",
    "bytes_all_byte_values",
    "bytes_repeated_nulls",
    "bytes_long",
    "list_empty",
    "list_simple",
    "list_single",
    "list_mixed",
    "list_nested",
    "list_deep_nested",
    "list_large",
    "tuple_empty",
    "tuple_single",
    "tuple_mixed",
    "tuple_nested",
    "tuple_large",
    "dict_empty",
    "dict_simple",
    "dict_string_keys",
    "dict_int_keys",
    "dict_of_lists",
    "dict_nested",
    "dict_keys_order1",
    "dict_keys_order2",
    "dict_different_insertion_order",
    "dict_large",
    "set_empty",
    "set_simple",
    "set_ints",
    "set_large_ints",
    "frozenset_empty",
    "frozenset_large_ints",
    "nested_mixed",
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
    "unsupported_ordered_dict",
    "unsupported_counter",
    "unsupported_defaultdict",
    "unsupported_namedtuple",
    "unsupported_datetime",
    "unsupported_datetime_min",
    "unsupported_datetime_max",
    "unsupported_decimal",
    "unsupported_decimal_max",
    "unsupported_decimal_min",
    "unsupported_uuid",
)


LOSSY_CASE_IDS = (
    "bytearray_empty",
    "bytearray_simple",
    "bytearray_all_byte_values",
)


BOUNDARY_CASE_IDS = (
    "int_negative_one",
    "int_min_64",
    "int_zero",
    "int_one",
    "int_255",
    "int_256",
    "int_2_31_minus_1",
    "int_2_31",
    "int_2_63_minus_1",
    "int_2_63",
    "int_huge",
    "int_negative_huge",
    "float_zero",
    "float_negative_zero",
    "float_one",
    "float_negative_one",
    "float_max_finite",
    "float_min_positive",
    "float_subnormal",
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
    "bytes_repeated_nulls",
    "bytes_long",
    "list_empty",
    "list_single",
    "list_mixed",
    "list_nested",
    "list_deep_nested",
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


# Build a fresh Python object for each stable test case identifier.
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
    if case_id == "int_regular":
        return 42
    if case_id == "int_zero":
        return 0
    if case_id == "int_one":
        return 1
    if case_id == "int_negative_one":
        return -1
    if case_id == "int_min_64":
        return -(2**63)
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
    if case_id == "int_negative_huge":
        return -(2**4096 + 123456789)
    if case_id == "float_pi":
        return 3.14159
    if case_id == "float_zero":
        return 0.0
    if case_id == "float_negative_zero":
        return -0.0
    if case_id == "float_one":
        return 1.0
    if case_id == "float_negative_one":
        return -1.0
    if case_id == "float_max_finite":
        return sys.float_info.max
    if case_id == "float_min_positive":
        return sys.float_info.min
    if case_id == "float_subnormal":
        return 5e-324
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
    if case_id == "string_hello":
        return "hello world"
    if case_id == "string_unicode":
        return "unicode-\u6d4b\u8bd5-\u03c0"
    if case_id == "string_chinese":
        return "\u4f60\u597d\uff0c\u4e16\u754c"
    if case_id == "string_emoji":
        return "emoji-\U0001f600-\U0001f680"
    if case_id == "string_long":
        return "abc123-" * 1000
    if case_id == "path_windows_like":
        return r"C:\Users\example\Desktop\software-testing"
    if case_id == "path_posix_like":
        return "/home/example/software-testing"
    if case_id == "bytes_empty":
        return b""
    if case_id == "bytes_null":
        return b"\x00inside\x00"
    if case_id == "bytes_all_byte_values":
        return bytes(range(256))
    if case_id == "bytes_repeated_nulls":
        return b"\x00" * 4096
    if case_id == "bytes_long":
        return bytes([index % 251 for index in range(4096)])
    if case_id == "bytearray_empty":
        return bytearray()
    if case_id == "bytearray_simple":
        return bytearray(b"mutable bytes")
    if case_id == "bytearray_all_byte_values":
        return bytearray(range(256))
    if case_id == "list_empty":
        return []
    if case_id == "list_simple":
        return [1, 2, 3]
    if case_id == "list_single":
        return [1]
    if case_id == "list_mixed":
        return [None, True, 123, -0.0, "text", b"bytes"]
    if case_id == "list_nested":
        return [[1, 2], ["a", {"nested": (3, 4)}], []]
    if case_id == "list_deep_nested":
        value = "leaf"
        for _ in range(64):
            value = [value]
        return value
    if case_id == "list_large":
        return list(range(2048))
    if case_id == "tuple_empty":
        return ()
    if case_id == "tuple_single":
        return (1,)
    if case_id == "tuple_mixed":
        return (1, "a", 3.14)
    if case_id == "tuple_nested":
        return ((1, 2), ("a", "b"), (None, False))
    if case_id == "tuple_large":
        return tuple(range(2048))
    if case_id == "dict_empty":
        return {}
    if case_id == "dict_simple":
        return {"key": "value", "num": 10}
    if case_id == "dict_string_keys":
        return {"alpha": 1, "beta": [2, 3], "gamma": None}
    if case_id == "dict_int_keys":
        return {0: "zero", -1: "minus one", 2**31: "large"}
    if case_id == "dict_of_lists":
        return {"numbers": [1, 2, 3], "letters": ["a", "b", "c"]}
    if case_id == "dict_nested":
        return {"outer": {"inner": [1, 2, {"leaf": True}]}}
    if case_id == "dict_keys_order1":
        return {"alpha": 1, "beta": 2, "gamma": 3}
    if case_id == "dict_keys_order2":
        data = {}
        data["gamma"] = 3
        data["beta"] = 2
        data["alpha"] = 1
        return data
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
    if case_id == "set_simple":
        return {1, 2, 3}
    if case_id == "set_ints":
        return {1, 2, 3, 255, 256}
    if case_id == "set_large_ints":
        return set(range(1024))
    if case_id == "frozenset_empty":
        return frozenset()
    if case_id == "frozenset_large_ints":
        return frozenset(range(1024))
    if case_id == "nested_mixed":
        return {"a": [1, {"b": 2}], "c": (3, 4)}
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
    if case_id == "unsupported_ordered_dict":
        return OrderedDict([("a", 1), ("b", 2)])
    if case_id == "unsupported_counter":
        return Counter(["a", "b", "a"])
    if case_id == "unsupported_defaultdict":
        return defaultdict(int, {"a": 1})
    if case_id == "unsupported_namedtuple":
        return _UnsupportedNamedTuple(1)
    if case_id == "unsupported_datetime":
        return datetime.datetime(2025, 5, 20, 10, 30)
    if case_id == "unsupported_datetime_min":
        return datetime.datetime.min
    if case_id == "unsupported_datetime_max":
        return datetime.datetime.max
    if case_id == "unsupported_decimal":
        return decimal.Decimal("3.14159")
    if case_id == "unsupported_decimal_max":
        return decimal.Decimal("1E+1000")
    if case_id == "unsupported_decimal_min":
        return decimal.Decimal("-1E+1000")
    if case_id == "unsupported_uuid":
        return uuid.UUID("12345678123456781234567812345678")

    raise KeyError(f"unknown specimen case_id: {case_id}")


# These display sample groups mirror representative values from the case-id based test suite above. 
# They make console output and report screenshots easier to read; 
# the full automated tests still use VALID_CASE_IDS, INVALID_CASE_IDS,
# BOUNDARY_CASE_IDS, and the fuzzing generators.
# Provide readable representative samples for equivalence-class evidence.
def equivalence_class_samples():
    """Return display samples for equivalence-class report evidence."""
    recursive_list = []
    recursive_list.append(recursive_list)
    return OrderedDict(
        [
            ("int", 42),
            ("float", 3.14159),
            ("str", "hello world"),
            ("unicode_str", "\u4f60\u597d\uff0c\u4e16\u754c"),
            ("list", [1, 2, 3]),
            ("dict", {"key": "value", "num": 10}),
            ("tuple", (1, "a", 3.14)),
            ("seg", ("c", "a", "b")),
            ("set", {1, 2, 3}),
            ("bool", True),
            ("none", None),
            ("nested", {"a": [1, {"b": 2}], "c": (3, 4)}),
            ("ordered_dict", OrderedDict([("a", 1), ("b", 2)])),
            ("recursive_list", recursive_list),
            ("custom_class", _UnsupportedClass()),
            ("datetime", datetime.datetime(2025, 5, 20, 10, 30)),
            ("decimal", decimal.Decimal("3.14159")),
            ("uuid", uuid.UUID("12345678123456781234567812345678")),
        ]
    )


# Provide readable representative samples for boundary-value evidence.
def boundary_value_samples():
    """Return display samples for boundary-value report evidence."""
    deep_nested_list = "leaf"
    for _ in range(64):
        deep_nested_list = [deep_nested_list]

    return OrderedDict(
        [
            ("max_int", 2**63 - 1),
            ("min_int", -(2**63)),
            ("zero", 0),
            ("long_str", "abc123-" * 1000),
            ("empty_str", ""),
            ("empty_list", []),
            ("large_list", list(range(2048))),
            ("empty_dict", {}),
            ("max_float", float("inf")),
            ("min_float", float("-inf")),
            ("nan_float", float("nan")),
            ("decimal_max", decimal.Decimal("1E+1000")),
            ("decimal_min", decimal.Decimal("-1E+1000")),
            ("deep_nested_list", deep_nested_list),
            ("long_tuple", tuple(range(1000))),
            ("long_bytes", b"\x00" * 4096),
            ("oldest_date", datetime.datetime.min),
            ("future_date", datetime.datetime.max),
        ]
    )


# Provide deterministic fuzz-like samples for evidence output.
def fuzzing_display_samples():
    """Return deterministic fuzzing examples for readable report evidence."""
    return OrderedDict(
        [
            (
                "fuzz_0",
                {
                    "module": "marshal",
                    "active": True,
                    "data": [None, 21, 1, "NaN", "tag-L", 82],
                    "payload": {
                        "=[\n1R": None,
                        "a'}G": None,
                        "mNxEA": "<marshal\nbytes>",
                    },
                },
            ),
            (
                "fuzz_1",
                {
                    "module": "marshal",
                    "active": False,
                    "data": ["e3kR?'Ffg-\"XB^F\nC~Gv&"],
                },
            ),
            ("fuzz_2", ["<@rHLd29n", 581, {"edge": "unicode-\u6d4b\u8bd5"}]),
        ]
    )


def all_valid_case_ids():
    return VALID_CASE_IDS


def all_invalid_case_ids():
    return INVALID_CASE_IDS


def all_lossy_case_ids():
    return LOSSY_CASE_IDS


def all_boundary_case_ids():
    return BOUNDARY_CASE_IDS
