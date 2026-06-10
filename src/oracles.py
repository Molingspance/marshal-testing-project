"""Test oracles for Python's marshal module.

The project needs stronger checks than plain equality because marshal supports
special floats, recursive containers, shared references, and code objects.
"""

import hashlib
import marshal
import math
import types


REASONABLE_EXCEPTIONS = (EOFError, TypeError, ValueError, RecursionError)


class _ComparisonState:
    def __init__(self, left_to_right=None, right_to_left=None):
        self.left_to_right = dict(left_to_right or {})
        self.right_to_left = dict(right_to_left or {})

    def clone(self):
        return _ComparisonState(self.left_to_right, self.right_to_left)

    def replace_with(self, other):
        self.left_to_right = dict(other.left_to_right)
        self.right_to_left = dict(other.right_to_left)


def sha256_bytes(data):
    """Return the SHA-256 hex digest for a byte-like object."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError("sha256_bytes expects a byte-like object")
    return hashlib.sha256(bytes(data)).hexdigest()


def equivalent(left, right):
    """Return True when two objects are equivalent for marshal testing.

    The comparison preserves recursive shape and shared references for mutable
    containers while handling NaN and signed zero explicitly.
    """
    return _equivalent(left, right, _ComparisonState())


def assert_roundtrip(value):
    """Assert that loads(dumps(value)) is equivalent to value."""
    dumped = marshal.dumps(value)
    loaded = marshal.loads(dumped)
    if not equivalent(value, loaded):
        raise AssertionError(
            "marshal round-trip changed value: "
            f"{describe_value(value)} -> {describe_value(loaded)}"
        )
    return loaded


def assert_file_roundtrip(value):
    """Assert the dump/load file API round-trips a value."""
    import io

    stream = io.BytesIO()
    marshal.dump(value, stream)
    stream.seek(0)
    loaded = marshal.load(stream)
    if not equivalent(value, loaded):
        raise AssertionError(
            "marshal file round-trip changed value: "
            f"{describe_value(value)} -> {describe_value(loaded)}"
        )
    return loaded


def assert_stable_dumps(value, repeats=3):
    """Assert repeated dumps in one process produce identical byte streams."""
    if repeats < 2:
        raise ValueError("repeats must be at least 2")

    dumps = [marshal.dumps(value) for _ in range(repeats)]
    hashes = [sha256_bytes(item) for item in dumps]
    if len(set(hashes)) != 1:
        raise AssertionError(
            "marshal.dumps was not stable in one process: "
            f"{hashes} for {describe_value(value)}"
        )
    return hashes


def assert_raises_reasonable_exception(callable_object):
    """Assert a negative test raises a controlled Python exception."""
    try:
        callable_object()
    except REASONABLE_EXCEPTIONS as exc:
        return exc
    except Exception as exc:  # pragma: no cover - only reached on failures.
        raise AssertionError(
            f"unexpected exception type: {type(exc).__name__}: {exc}"
        ) from exc

    raise AssertionError(
        "expected a reasonable exception, but none was raised"
    )


def describe_value(value, limit=160):
    """Return a compact description for diagnostics and result logs."""
    if isinstance(value, types.CodeType):
        text = (
            f"<code {value.co_name} at "
            f"{value.co_filename}:{value.co_firstlineno}>"
        )
    else:
        try:
            text = repr(value)
        except Exception:
            text = object.__repr__(value)
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return f"{type(value).__name__} {text}"


def _equivalent(left, right, state):
    if left is None or right is None:
        return left is right
    if left is Ellipsis or right is Ellipsis:
        return left is right
    if left is StopIteration or right is StopIteration:
        return left is StopIteration and right is StopIteration
    if type(left) is not type(right):
        return False

    if isinstance(left, bool):
        return left is right
    if isinstance(left, int):
        return left == right
    if isinstance(left, float):
        return _floats_equivalent(left, right)
    if isinstance(left, complex):
        return (
            _floats_equivalent(left.real, right.real)
            and _floats_equivalent(left.imag, right.imag)
        )
    if isinstance(left, (str, bytes, bytearray)):
        return left == right

    if isinstance(left, list):
        seen = _register_pair(left, right, state)
        if seen is not None:
            return seen
        return _sequences_equivalent(left, right, state)

    if isinstance(left, tuple):
        return _sequences_equivalent(left, right, state)

    if isinstance(left, dict):
        seen = _register_pair(left, right, state)
        if seen is not None:
            return seen
        return _dicts_equivalent(left, right, state)

    if isinstance(left, set):
        seen = _register_pair(left, right, state)
        if seen is not None:
            return seen
        return _sets_equivalent(left, right, state)

    if isinstance(left, frozenset):
        return _sets_equivalent(left, right, state)

    if isinstance(left, types.CodeType):
        seen = _register_pair(left, right, state)
        if seen is not None:
            return seen
        return _code_objects_equivalent(left, right, state)

    return left == right


def _register_pair(left, right, state):
    left_id = id(left)
    right_id = id(right)
    mapped_right = state.left_to_right.get(left_id)
    mapped_left = state.right_to_left.get(right_id)

    if mapped_right is not None or mapped_left is not None:
        return mapped_right == right_id and mapped_left == left_id

    state.left_to_right[left_id] = right_id
    state.right_to_left[right_id] = left_id
    return None


def _floats_equivalent(left, right):
    if math.isnan(left) or math.isnan(right):
        return math.isnan(left) and math.isnan(right)
    if left == 0.0 and right == 0.0:
        return math.copysign(1.0, left) == math.copysign(1.0, right)
    return left == right


def _sequences_equivalent(left, right, state):
    if len(left) != len(right):
        return False
    for left_item, right_item in zip(left, right):
        if not _equivalent(left_item, right_item, state):
            return False
    return True


def _dicts_equivalent(left, right, state):
    if len(left) != len(right):
        return False

    unmatched = list(right.items())
    for left_key, left_value in left.items():
        match_index = None
        match_state = None
        for index, (right_key, right_value) in enumerate(unmatched):
            trial_state = state.clone()
            if _equivalent(left_key, right_key, trial_state) and _equivalent(
                left_value, right_value, trial_state
            ):
                match_index = index
                match_state = trial_state
                break
        if match_index is None:
            return False
        state.replace_with(match_state)
        del unmatched[match_index]
    return True


def _sets_equivalent(left, right, state):
    if len(left) != len(right):
        return False

    unmatched = list(right)
    for left_item in left:
        match_index = None
        match_state = None
        for index, right_item in enumerate(unmatched):
            trial_state = state.clone()
            if _equivalent(left_item, right_item, trial_state):
                match_index = index
                match_state = trial_state
                break
        if match_index is None:
            return False
        state.replace_with(match_state)
        del unmatched[match_index]
    return True


def _code_objects_equivalent(left, right, state):
    scalar_attrs = (
        "co_argcount",
        "co_posonlyargcount",
        "co_kwonlyargcount",
        "co_nlocals",
        "co_stacksize",
        "co_flags",
        "co_code",
        "co_names",
        "co_varnames",
        "co_filename",
        "co_name",
        "co_qualname",
        "co_firstlineno",
        "co_lnotab",
        "co_linetable",
        "co_exceptiontable",
        "co_freevars",
        "co_cellvars",
    )
    for attr in scalar_attrs:
        sentinel = object()
        left_value = getattr(left, attr, sentinel)
        right_value = getattr(right, attr, sentinel)
        if left_value != right_value:
            return False

    return _equivalent(left.co_consts, right.co_consts, state)
