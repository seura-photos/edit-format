# Seura Edit Format — guide for Claude Code

This repository defines an open file format, not an app. Precision and backward compatibility matter more than anything else: other apps may implement it, and users' edits depend on it.

- `spec/edit-format.md` is the source of truth. `schema/1.0.json`, `examples/`, `tests/valid/`, `tests/invalid/`, and `tools/check.py` must always agree with it.
- `schema/1.x-reader.json` is generated: after changing `schema/1.0.json`, run `python tools/make_reader_schema.py`. Never edit it by hand.
- When the spec changes, update the schema, examples, and tests in the same change, then run `python tools/check.py --self-test`; it must pass.
- Every new rule gets at least one file in `tests/invalid/` that breaks only that rule.
- Never change the meaning of an existing operation version or of format version 1.0 once released. Changes go in a new operation version or a new format version, as the spec's versioning section describes.
- Keep examples realistic: full 64-character hashes, values within range, operations in canonical order.
