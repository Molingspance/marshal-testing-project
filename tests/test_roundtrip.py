import unittest

from src.oracles import assert_file_roundtrip, assert_roundtrip, assert_stable_dumps
from src.specimens import all_valid_case_ids, build_specimen


class RoundTripTests(unittest.TestCase):
    def test_all_valid_specimens_roundtrip(self):
        for case_id in all_valid_case_ids():
            with self.subTest(case_id=case_id):
                assert_roundtrip(build_specimen(case_id))

    def test_all_valid_specimens_stable_in_process(self):
        for case_id in all_valid_case_ids():
            with self.subTest(case_id=case_id):
                assert_stable_dumps(build_specimen(case_id), repeats=5)

    def test_file_api_roundtrip(self):
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


if __name__ == "__main__":
    unittest.main()

