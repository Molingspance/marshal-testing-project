import marshal
import unittest

from src.fuzz_generator import summarize_lexical_fuzz
from src.oracles import assert_raises_reasonable_exception
from src.specimens import all_invalid_case_ids, build_specimen


# Validate that unsupported objects and malformed byte streams fail cleanly.
class BlackBoxInvalidInputTests(unittest.TestCase):
    def test_unsupported_objects_raise_exceptions(self):
        for case_id in all_invalid_case_ids():
            with self.subTest(case_id=case_id):
                value = build_specimen(case_id)
                try:
                    assert_raises_reasonable_exception(lambda: marshal.dumps(value))
                finally:
                    close = getattr(value, "close", None)
                    if close is not None:
                        close()

    def test_corrupted_streams_raise_exceptions(self):
        streams = {
            "empty": b"",
            "nul": b"\x00",
            "invalid-tag": b"\xff",
            "truncated-int": marshal.dumps(123456)[:2],
            "truncated-list": marshal.dumps([1, 2, 3])[:-1],
            "modified-first-byte": b"\xff" + marshal.dumps({"a": 1})[1:],
        }
        for name, data in streams.items():
            with self.subTest(name=name):
                assert_raises_reasonable_exception(lambda: marshal.loads(data))

    def test_lexical_fuzzing_handles_mutated_streams(self):
        summary = summarize_lexical_fuzz()
        self.assertGreater(summary["total"], 0)
        self.assertGreater(
            sum(summary["exceptions"].values()),
            0,
            "lexical fuzzing should exercise exception paths",
        )


if __name__ == "__main__":
    unittest.main()
