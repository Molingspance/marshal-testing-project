import unittest

from src.oracles import assert_roundtrip, assert_stable_dumps
from src.specimens import all_boundary_case_ids, build_specimen


class BlackBoxBoundaryValueTests(unittest.TestCase):
    def test_boundary_values_roundtrip(self):
        for case_id in all_boundary_case_ids():
            with self.subTest(case_id=case_id):
                assert_roundtrip(build_specimen(case_id))

    def test_boundary_values_stable_in_process(self):
        for case_id in all_boundary_case_ids():
            with self.subTest(case_id=case_id):
                assert_stable_dumps(build_specimen(case_id), repeats=5)


if __name__ == "__main__":
    unittest.main()
