import inspect
import marshal
import unittest

from src.oracles import assert_raises_reasonable_exception, assert_roundtrip
from src.specimens import build_specimen


# Detect whether the current Python exposes marshal's allow_code argument.
def supports_allow_code():
    try:
        signature = inspect.signature(marshal.dumps)
    except (TypeError, ValueError):
        return False
    return "allow_code" in signature.parameters


# Exercise representative marshal branch and decision outcomes.
class MarshalBranchCoverageTests(unittest.TestCase):
    def test_supported_and_unsupported_dump_paths(self):
        supported = build_specimen("dict_nested")
        assert_roundtrip(supported)

        unsupported = build_specimen("unsupported_object")
        assert_raises_reasonable_exception(lambda: marshal.dumps(unsupported))

    def test_valid_and_invalid_load_paths(self):
        valid_stream = marshal.dumps({"ok": [1, 2, 3]})
        self.assertEqual(marshal.loads(valid_stream), {"ok": [1, 2, 3]})

        invalid_streams = (
            b"",
            b"\xff",
            marshal.dumps(123456)[:2],
            marshal.dumps([1, 2, 3])[:-1],
        )
        for data in invalid_streams:
            with self.subTest(data=data):
                assert_raises_reasonable_exception(lambda: marshal.loads(data))

    def test_recursive_and_non_recursive_container_paths(self):
        normal = assert_roundtrip([1, 2, 3])
        self.assertEqual(normal, [1, 2, 3])

        recursive_list = assert_roundtrip(build_specimen("recursive_list"))
        self.assertIs(recursive_list[0], recursive_list)

        recursive_dict = assert_roundtrip(build_specimen("recursive_dict"))
        self.assertIs(recursive_dict["self"], recursive_dict)

        shared = assert_roundtrip(build_specimen("shared_reference_list"))
        self.assertIs(shared[0], shared[1])

    def test_format_version_paths(self):
        value = {"text": "marshal", "numbers": [0, 255, 256, 2**31]}

        for version in range(marshal.version + 1):
            with self.subTest(version=version):
                dumped = marshal.dumps(value, version)
                loaded = marshal.loads(dumped)
                self.assertEqual(loaded, value)

    def test_code_object_allow_and_reject_paths(self):
        code_object = build_specimen("code_object_simple")
        assert_roundtrip(code_object)

        if not supports_allow_code():
            self.skipTest("allow_code branch is only available in newer Python")

        assert_raises_reasonable_exception(
            lambda: marshal.dumps(code_object, allow_code=False)
        )


if __name__ == "__main__":
    unittest.main()
