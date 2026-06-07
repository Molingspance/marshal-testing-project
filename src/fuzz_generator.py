"""Generation-based and lexical fuzzing helpers for marshal."""

import marshal
import random
import string

from src.oracles import (
    assert_roundtrip,
    assert_stable_dumps,
    describe_value,
    sha256_bytes,
)


DEFAULT_SEED = 20260607
DEFAULT_CASES = 1000


def iter_generated_cases(
    count=DEFAULT_CASES,
    seed=DEFAULT_SEED,
    max_depth=4,
    max_container_size=8,
    max_string_len=256,
    max_bytes_len=256,
):
    """Yield deterministic pseudo-random legal marshal values."""
    rng = random.Random(seed)
    for index in range(count):
        yield index, generate_value(
            rng,
            max_depth=max_depth,
            max_container_size=max_container_size,
            max_string_len=max_string_len,
            max_bytes_len=max_bytes_len,
        )


def run_generation_fuzz(count=DEFAULT_CASES, seed=DEFAULT_SEED):
    """Run round-trip and same-process stability checks for generated values."""
    failures = []
    for index, value in iter_generated_cases(count=count, seed=seed):
        try:
            assert_roundtrip(value)
            hashes = assert_stable_dumps(value, repeats=3)
        except Exception as exc:
            failures.append(
                {
                    "seed": seed,
                    "case_index": index,
                    "value": describe_value(value),
                    "exception_type": type(exc).__name__,
                    "exception": str(exc),
                }
            )
        else:
            if len(set(hashes)) != 1:
                failures.append(
                    {
                        "seed": seed,
                        "case_index": index,
                        "value": describe_value(value),
                        "exception_type": "NonDeterministicHash",
                        "exception": repr(hashes),
                    }
                )
    return failures


def generate_value(
    rng,
    max_depth=4,
    max_container_size=8,
    max_string_len=256,
    max_bytes_len=256,
):
    """Generate one legal marshal value from a recursive grammar."""
    if max_depth <= 0:
        return generate_scalar(rng, max_string_len, max_bytes_len)

    choices = (
        "scalar",
        "list",
        "tuple",
        "dict",
        "set",
        "frozenset",
    )
    choice = rng.choice(choices)
    if choice == "scalar":
        return generate_scalar(rng, max_string_len, max_bytes_len)

    size = rng.randint(0, max_container_size)
    if choice == "list":
        return [
            generate_value(
                rng,
                max_depth - 1,
                max_container_size,
                max_string_len,
                max_bytes_len,
            )
            for _ in range(size)
        ]
    if choice == "tuple":
        return tuple(
            generate_value(
                rng,
                max_depth - 1,
                max_container_size,
                max_string_len,
                max_bytes_len,
            )
            for _ in range(size)
        )
    if choice == "dict":
        return {
            generate_hashable_scalar(rng, max_string_len, max_bytes_len): generate_value(
                rng,
                max_depth - 1,
                max_container_size,
                max_string_len,
                max_bytes_len,
            )
            for _ in range(size)
        }
    if choice == "set":
        return {
            generate_hashable_scalar(rng, max_string_len, max_bytes_len)
            for _ in range(size)
        }
    return frozenset(
        generate_hashable_scalar(rng, max_string_len, max_bytes_len)
        for _ in range(size)
    )


def generate_scalar(rng, max_string_len=256, max_bytes_len=256):
    choice = rng.choice(
        (
            "none",
            "bool",
            "int",
            "float",
            "special_float",
            "str",
            "bytes",
        )
    )
    if choice == "none":
        return None
    if choice == "bool":
        return rng.choice((True, False))
    if choice == "int":
        return rng.randint(-(2**80), 2**80)
    if choice == "float":
        return rng.uniform(-1.0e12, 1.0e12)
    if choice == "special_float":
        return rng.choice((0.0, -0.0, float("inf"), float("-inf"), float("nan")))
    if choice == "str":
        return _random_string(rng, max_string_len)
    return _random_bytes(rng, max_bytes_len)


def generate_hashable_scalar(rng, max_string_len=256, max_bytes_len=256):
    choice = rng.choice(("none", "bool", "int", "float", "str", "bytes"))
    if choice == "none":
        return None
    if choice == "bool":
        return rng.choice((True, False))
    if choice == "int":
        return rng.randint(-(2**48), 2**48)
    if choice == "float":
        return rng.uniform(-1.0e6, 1.0e6)
    if choice == "str":
        return _random_string(rng, max_string_len)
    return _random_bytes(rng, max_bytes_len)


def mutated_streams(seed=DEFAULT_SEED):
    """Yield mutated marshal byte streams for lexical fuzzing."""
    rng = random.Random(seed)
    bases = (
        ("none", marshal.dumps(None)),
        ("int", marshal.dumps(123456)),
        ("list", marshal.dumps([1, 2, 3])),
        ("dict", marshal.dumps({"a": 1})),
        ("code", marshal.dumps((lambda value: value + 1).__code__)),
    )

    for name, data in bases:
        if data:
            yield f"{name}:truncate", data[:-1]
            yield f"{name}:drop-first", data[1:]
            yield f"{name}:replace-tag", bytes([0xFF]) + data[1:]
            index = rng.randrange(len(data))
            bit = 1 << rng.randrange(8)
            flipped = bytearray(data)
            flipped[index] ^= bit
            yield f"{name}:flip-bit-{index}", bytes(flipped)
        yield f"{name}:insert-byte", b"\x00" + data
        suffix = bytes(rng.randrange(256) for _ in range(8))
        yield f"{name}:random-suffix", data + suffix


def summarize_lexical_fuzz(seed=DEFAULT_SEED):
    """Run lexical fuzzing and return exception/success counts."""
    summary = {
        "loaded_cases": [],
        "seed": seed,
        "total": 0,
        "exceptions": {},
        "loaded": 0,
        "loaded_hashes": [],
    }
    for name, data in mutated_streams(seed=seed):
        summary["total"] += 1
        try:
            loaded = marshal.loads(data)
        except Exception as exc:
            exc_name = type(exc).__name__
            summary["exceptions"][exc_name] = (
                summary["exceptions"].get(exc_name, 0) + 1
            )
        else:
            summary["loaded"] += 1
            summary["loaded_cases"].append(
                {
                    "name": name,
                    "value": describe_value(loaded),
                }
            )
            try:
                summary["loaded_hashes"].append(sha256_bytes(marshal.dumps(loaded)))
            except Exception:
                summary["loaded_hashes"].append("<unmarshallable-loaded-value>")
    return summary


def _random_string(rng, max_length):
    alphabet = string.ascii_letters + string.digits + " _-:\n\t"
    length = rng.randint(0, max_length)
    return "".join(rng.choice(alphabet) for _ in range(length))


def _random_bytes(rng, max_length):
    length = rng.randint(0, max_length)
    return bytes(rng.randrange(256) for _ in range(length))
