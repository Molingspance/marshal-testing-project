import marshal
import math
import unittest

from src.oracles import assert_raises_reasonable_exception, assert_roundtrip
from src.specimens import build_specimen


# Exercise representative marshal conditions and edge predicates.
class MarshalConditionCoverageTests(unittest.TestCase):
    def test_nan_and_non_nan_float_paths(self):
        nan_loaded = marshal.loads(marshal.dumps(float("nan")))
        self.assertTrue(math.isnan(nan_loaded))

        normal_loaded = marshal.loads(marshal.dumps(1.5))
        self.assertEqual(normal_loaded, 1.5)

    def test_positive_and_negative_zero_paths(self):
        negative_zero = marshal.loads(marshal.dumps(-0.0))
        positive_zero = marshal.loads(marshal.dumps(0.0))

        self.assertEqual(math.copysign(1.0, negative_zero), -1.0)
        self.assertEqual(math.copysign(1.0, positive_zero), 1.0)

    def test_empty_and_non_empty_container_paths(self):
        self.assertEqual(marshal.loads(marshal.dumps([])), [])
        self.assertEqual(marshal.loads(marshal.dumps([1])), [1])

        self.assertEqual(marshal.loads(marshal.dumps({})), {})
        self.assertEqual(marshal.loads(marshal.dumps({"a": 1})), {"a": 1})

    def test_recursive_and_non_recursive_conditions(self):
        non_recursive = marshal.loads(marshal.dumps([1, 2, 3]))
        self.assertEqual(non_recursive, [1, 2, 3])

        recursive = assert_roundtrip(build_specimen("recursive_list"))
        self.assertIs(recursive[0], recursive)

    def test_invalid_tag_and_truncated_stream_conditions(self):
        assert_raises_reasonable_exception(lambda: marshal.loads(b"\xff"))

        truncated = marshal.dumps({"a": [1, 2, 3]})[:-1]
        assert_raises_reasonable_exception(lambda: marshal.loads(truncated))

    def test_complete_stream_with_and_without_trailing_data(
        self,
    ):
        dumped = marshal.dumps(123456)

        self.assertEqual(marshal.loads(dumped), 123456)
        self.assertEqual(marshal.loads(dumped + b"trailing"), 123456)


if __name__ == "__main__":
    unittest.main()
