import marshal
import unittest

from src.specimens import all_lossy_case_ids, build_specimen


# Document supported-but-lossy marshal behavior such as bytearray loading.
class BlackBoxSpecialBehaviorTests(unittest.TestCase):
    def test_bytearray_loads_as_bytes(self):
        for case_id in all_lossy_case_ids():
            with self.subTest(case_id=case_id):
                value = build_specimen(case_id)
                loaded = marshal.loads(marshal.dumps(value))
                self.assertIsInstance(loaded, bytes)
                self.assertEqual(loaded, bytes(value))


if __name__ == "__main__":
    unittest.main()
