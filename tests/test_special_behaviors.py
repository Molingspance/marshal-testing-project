import marshal
import unittest

from src.specimens import all_lossy_case_ids, build_specimen


class SpecialBehaviorTests(unittest.TestCase):
    def test_bytearray_values_load_as_bytes(self):
        for case_id in all_lossy_case_ids():
            with self.subTest(case_id=case_id):
                value = build_specimen(case_id)
                loaded = marshal.loads(marshal.dumps(value))
                self.assertIsInstance(loaded, bytes)
                self.assertEqual(loaded, bytes(value))


if __name__ == "__main__":
    unittest.main()
