# Seura Edit Format — guide for Claude Code

This repository defines an open file format, not an app. Precision and backward compatibility matter more than anything else: other apps may implement it, and users' edits depend on it.

**Who changes what:** the format is designed in Nevada's design sessions with Claude in the Claude app. Claude Code, implementing it in `seura-photos/seura`, raises gaps and questions there rather than changing the format's meaning itself. Typos, broken links, and tooling fixes are fine to send as pull requests directly.

**The formulas appendix** (the exact math for each core operation, which the spec promises "alongside the reference implementation") is the exception: Claude Code writes it, one operation per pull request, as Seura Photos implements that operation. Each entry describes the math in words and pseudocode, not by pointing at shader code, with reference images and expected results and the tolerance an implementation must meet. The design session reviews each pull request, and the whole appendix again before the format is frozen at 1.0. Changing an operation's meaning, rather than writing down what it already means, still goes to a design session first.

- `spec/edit-format.md` is the source of truth. `schema/1.0.json`, `examples/`, `tests/valid/`, `tests/invalid/`, and `tools/check.py` must always agree with it.
- `schema/1.x-reader.json` is generated: after changing `schema/1.0.json`, run `python tools/make_reader_schema.py`. Never edit it by hand.
- When the spec changes, update the schema, examples, and tests in the same change, then run `python tools/check.py --self-test`; it must pass.
- Every new rule gets at least one file in `tests/invalid/` that breaks only that rule.
- Never change the meaning of an existing operation version or of format version 1.0 once released. Changes go in a new operation version or a new format version, as the spec's versioning section describes.
- Keep examples realistic: full 64-character hashes, values within range, operations in canonical order.
