# Statement Coverage Example

Target function:

- `src/oracles.py::_register_pair`

Statement lines:

- `[174, 175, 176, 177, 179, 180, 182, 183, 184]`

Test case 1:

- description: first visit of a new left/right object pair
- covered lines: `[174, 175, 176, 177, 179, 182, 183, 184]`
- statement coverage: `88.89%`

Test case 2:

- description: revisit of an already registered left/right object pair
- covered lines: `[174, 175, 176, 177, 179, 180]`
- statement coverage: `66.67%`

Combined result:

- covered lines: `[174, 175, 176, 177, 179, 180, 182, 183, 184]`
- statement coverage: `100.0%`

Interpretation:

- Test case 1 exercises the path where a left/right object pair is seen for the first time.
- Test case 2 exercises the path where the same pair has already been registered.
- Together, the two test cases cover all executable statements in `_register_pair`, giving 100% statement coverage for this representative white-box target.
