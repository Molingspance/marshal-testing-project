import unittest

from src.oracles import _ComparisonState, _register_pair


class StatementCoverageExampleTests(unittest.TestCase):
    def test_register_pair_first_visit(self):
        left = []
        right = []
        state = _ComparisonState()

        result = _register_pair(left, right, state)

        self.assertIsNone(result)
        self.assertEqual(id(right), state.left_to_right[id(left)])
        self.assertEqual(id(left), state.right_to_left[id(right)])

    def test_register_pair_revisit(self):
        left = []
        right = []
        state = _ComparisonState(
            left_to_right={id(left): id(right)},
            right_to_left={id(right): id(left)},
        )

        result = _register_pair(left, right, state)

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
