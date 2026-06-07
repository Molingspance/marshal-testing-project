import os
import unittest

from src.fuzz_generator import DEFAULT_SEED, run_generation_fuzz


class GenerationFuzzingTests(unittest.TestCase):
    def test_generated_values_roundtrip_and_remain_stable(self):
        count = int(os.environ.get("MARSHAL_FUZZ_CASES", "1000"))
        failures = run_generation_fuzz(count=count, seed=DEFAULT_SEED)
        self.assertEqual([], failures, msg=str(failures[:3]))


if __name__ == "__main__":
    unittest.main()
