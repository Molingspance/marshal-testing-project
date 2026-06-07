# Exploratory Testing Sessions

## ET-1: `PYTHONHASHSEED` and unordered containers

- Charter: explore whether unordered containers keep hash-identical marshal bytes across subprocesses.
- Focus: `set_ints`, `set_strings`, `frozenset_strings`, and dictionary cases for contrast.
- Observation: string-based `set` and `frozenset` cases changed `sha256` across different `PYTHONHASHSEED` values, while ordered containers and integer-only cases remained stable.
- Follow-up: keep cross-process matrix evidence in `tools/run_subprocess_matrix.py` and report this as a stability limitation rather than a crash bug.

## ET-2: corrupted byte streams

- Charter: explore how `marshal.loads()` reacts to damaged or malformed byte streams.
- Focus: empty streams, invalid type tags, truncation, bit flips, inserted bytes, and random suffixes.
- Observation: most mutated streams raised controlled Python exceptions such as `EOFError`, `UnicodeDecodeError`, and `ValueError`; some mutations still decoded into valid objects, especially when the mutation accidentally created a different valid tag or appended trailing bytes after a complete object.
- Follow-up: keep both targeted negative tests and lexical fuzzing in the final suite.

## ET-3: special floating-point values

- Charter: explore corner cases where plain equality is not a good oracle.
- Focus: `NaN`, `Inf`, `-Inf`, and `-0.0`.
- Observation: `NaN != NaN`, so a normal equality oracle would produce false failures, and `-0.0` needs sign-sensitive comparison even though `-0.0 == 0.0`.
- Follow-up: use the custom float oracle in `src/oracles.py` and document why this oracle is necessary in the report.
