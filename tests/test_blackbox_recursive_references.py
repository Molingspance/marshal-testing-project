import unittest

from src.oracles import assert_roundtrip, equivalent
from src.specimens import build_specimen


# Validate recursive and shared-reference structures after marshal round trips.
class BlackBoxRecursiveReferenceTests(unittest.TestCase):
    def test_recursive_list_preserves_cycle(self):
        loaded = assert_roundtrip(build_specimen("recursive_list"))
        self.assertIs(loaded[0], loaded)

    def test_recursive_dict_preserves_cycle(self):
        loaded = assert_roundtrip(build_specimen("recursive_dict"))
        self.assertIs(loaded["self"], loaded)

    def test_indirect_recursive_list_preserves_cycle(self):
        loaded = assert_roundtrip(build_specimen("indirect_recursive_list"))
        self.assertIs(loaded[0][0], loaded)

    def test_shared_reference_preserves_aliasing(self):
        loaded = assert_roundtrip(build_specimen("shared_reference_list"))
        self.assertIs(loaded[0], loaded[1])

    def test_equivalence_handles_cycles(self):
        left = build_specimen("recursive_list")
        right = build_specimen("recursive_list")
        self.assertTrue(equivalent(left, right))


if __name__ == "__main__":
    unittest.main()
