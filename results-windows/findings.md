# Findings Summary

Environment used for the bundled local evidence:

- Python 3.9.15
- Windows

Main observations:

1. The local unit test suite passed without failures.
2. Same-process repeated `marshal.dumps()` calls were stable for the representative valid specimens.
3. The round-trip property held for the valid specimens, including recursive containers and shared references.
4. Lexical fuzzing generated 30 mutated byte streams:
   - 21 raised controlled Python exceptions (`EOFError`, `UnicodeDecodeError`, or `ValueError`);
   - 9 still decoded into valid objects because the mutation either created another valid tag sequence or appended trailing bytes after a complete value.
5. Generation-based fuzzing found no local counterexample in the configured run budget.

Interpretation:

- For malformed inputs, the main local risk is not a crash but that some byte mutations remain syntactically valid and therefore deserialize successfully into a different object.
- A difference across Python versions is not automatically a bug because the marshal format is intentionally version-dependent.
- Special values such as `NaN` and `-0.0` require custom oracles; plain equality is not sufficient.
