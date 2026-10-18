# Seura Edit Format

An open file format for non-destructive photo edits, tags, and ratings, stored in a small, readable JSON file beside each photo.

```
IMG_1234.jpg
IMG_1234.jpg.seura.json   ← crop, exposure, tags, rating, undo history
```

The original photo is never modified. Any app that implements this format can read, render, and continue editing the same files, so a user's work isn't locked into one program. The format was created for [Seura Photos](https://github.com/seura-photos/seura), but is meant for any app.

> **Status:** version 1.0, draft. Expect changes until Seura Photos 1.0 ships.

## Contents

| Path | What it is |
| --- | --- |
| [`spec/edit-format.md`](spec/edit-format.md) | The specification. Start here. |
| [`schema/1.0.json`](schema/1.0.json) | JSON Schema (2020-12) for format version 1.0. |
| [`schema/1.x-reader.json`](schema/1.x-reader.json) | Reader schema for files with a newer 1.x minor version: checks the 1.0 fields, accepts the rest. Generated from 1.0.json. |
| [`examples/`](examples/) | Valid example files: an edited photo, a tag-only file, a photo with undone changes ready to redo, and a preset. |
| [`tests/valid/`](tests/valid/) | Other files that must be accepted, such as one from a newer minor version. |
| [`tests/invalid/`](tests/invalid/) | Files that must be rejected, one rule each. |
| [`tools/check.py`](tools/check.py) | Validator: the schema plus the rules JSON Schema can't express (operation order, duplicates, tag case, undone records last). |
| [`tools/make_reader_schema.py`](tools/make_reader_schema.py) | Regenerates the reader schema after a change to 1.0.json. |

Planned: conformance tests with sample photos and expected output images, so other implementations can verify they render identically.

## Validating files

```
pip install jsonschema
python tools/check.py path/to/IMG_1234.jpg.seura.json
python tools/check.py --self-test
```

## In brief

- **Settings, not steps.** Each edit is stored as its current value and rendered in a fixed order, so the result never depends on the order the user clicked things.
- **Extensible.** Plugins and other apps add their own operations under a reverse-domain name, such as `com.example.filmGrain`. Readers keep what they don't understand.
- **Versioned.** Operations and the format itself carry version numbers, so old edits keep rendering the way the user left them.
- **Undo and redo that survive restarts.** A short history of changes is kept in the file.

## Licenses

- The specification (`spec/`) is licensed under [Creative Commons Attribution 4.0](LICENSE-SPEC).
- The schema, examples, tests, and tools are licensed under the [Apache License 2.0](LICENSE).
