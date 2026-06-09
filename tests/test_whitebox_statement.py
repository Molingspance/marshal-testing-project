import marshal
import unittest

from src.oracles import assert_file_roundtrip, assert_roundtrip, assert_stable_dumps
from src.specimens import build_specimen


class MarshalStatementCoverageTests(unittest.TestCase):
    def test_representative_type_write_read_paths(self):
        case_ids = (
            "none",
            "true",
            "false",
            "ellipsis",
            "stop_iteration",
            "int_zero",
            "int_255",
            "int_256",
            "int_2_31",
            "int_2_63",
            "int_huge",
            "float_negative_zero",
            "float_nan",
            "float_inf",
            "complex_with_nan",
            "string_empty",
            "string_unicode",
            "bytes_empty",
            "bytes_all_byte_values",
            "list_empty",
            "list_nested",
            "tuple_single",
            "tuple_nested",
            "dict_empty",
            "dict_nested",
            "set_empty",
            "set_ints",
            "frozenset_empty",
            "frozenset_large_ints",
            "code_object_simple",
        )

        for case_id in case_ids:
            with self.subTest(case_id=case_id):
                value = build_specimen(case_id)
                assert_roundtrip(value)
                assert_stable_dumps(value, repeats=3)

    def test_file_api_paths(self):
        case_ids = (
            "none",
            "int_huge",
            "float_negative_zero",
            "string_unicode",
            "bytes_all_byte_values",
            "list_nested",
            "dict_nested",
            "code_object_simple",
        )

        for case_id in case_ids:
            with self.subTest(case_id=case_id):
                assert_file_roundtrip(build_specimen(case_id))

    def test_bytes_like_write_path(self):
        value = bytearray(b"abc\x00xyz")
        loaded = marshal.loads(marshal.dumps(value))

        self.assertIsInstance(loaded, bytes)
        self.assertEqual(loaded, bytes(value))


if __name__ == "__main__":
    unittest.main()
