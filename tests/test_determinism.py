import unittest

from src.oracles import assert_stable_dumps
from src.specimens import all_determinism_case_ids, build_specimen


class DeterminismTests(unittest.TestCase):
    def test_repeated_dumps_are_hash_identical_in_one_process(self):
        for case_id in all_determinism_case_ids():
            with self.subTest(case_id=case_id):
                assert_stable_dumps(build_specimen(case_id), repeats=5)


if __name__ == "__main__":
    unittest.main()

