# Seura Edit Format, version 1.0

Status: draft · Last updated: 2026-10-17

This document defines the file format Seura Photos uses to store non-destructive edits, tags, and ratings beside each photo. It is written for anyone implementing the format, including other apps.

The key words MUST, MUST NOT, SHOULD, and MAY are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## Goals

The format exists so a user's work outlives any one app, including Seura Photos.

- **Readable.** Plain JSON a person can open and understand, with no compression or encoding.
- **Self-contained.** The current settings are stored in full, so a reader never needs to replay history to render a photo.
- **Predictable.** The same file renders the same image in every conforming app and every future version of Seura Photos.
- **Extensible.** New operations, including ones from plugins or other apps, can be added without breaking existing readers, and readers preserve what they don't understand.
- **Small.** A typical file is a few kilobytes.

## File basics

- **Name.** The photo's full file name plus `.seura.json`: `IMG_1234.jpg` → `IMG_1234.jpg.seura.json`. Keeping the photo's extension prevents collisions between `IMG_1234.jpg` and `IMG_1234.heic`.
- **Location.** The same folder as the photo, always.
- **Encoding.** UTF-8 JSON without a byte-order mark. Writers SHOULD indent with two spaces and end the file with a newline, so files stay readable and compare cleanly line by line.
- **One photo per file.** Each edit file describes exactly one photo.

## A complete example

A photo rotated, cropped, brightened, given more contrast and a slight tint, vignetted, tagged, and rated four stars. The last operation comes from a hypothetical plugin, to show how extensions sit alongside core operations. The same file is in [`examples/`](../examples/).

```json
{
  "$schema": "https://seuraphotos.app/schema/edit/1.0.json",
  "format": "seura-edit",
  "formatVersion": "1.0",
  "writer": { "app": "Seura Photos", "version": "1.0.0" },
  "modified": "2026-10-17T19:40:12Z",
  "photo": {
    "file": "IMG_1234.jpg",
    "size": 3482113,
    "sha256": "9f2c4e7a…",
    "width": 4032,
    "height": 3024
  },
  "operations": [
    { "id": "seura.orient", "version": 1, "params": { "rotate": 90, "flipH": false, "flipV": false } },
    { "id": "seura.crop", "version": 1, "params": { "x": 0.05, "y": 0.1, "width": 0.9, "height": 0.75, "aspect": "4:3" } },
    { "id": "seura.exposure", "version": 1, "params": { "ev": 0.3 } },
    { "id": "seura.whiteBalance", "version": 1, "params": { "temperature": 0, "tint": 5 } },
    { "id": "seura.contrast", "version": 1, "params": { "amount": 35 } },
    { "id": "seura.vignette", "version": 1, "params": { "amount": -25, "size": 60 } },
    { "id": "com.example.filmGrain", "version": 2, "group": "effects", "params": { "amount": 12 } }
  ],
  "tags": ["family/kids", "vacation/2026"],
  "rating": 4,
  "history": [
    { "at": "2026-10-17T19:38:02Z", "label": "Contrast", "changes": [ { "op": "seura.contrast", "from": null, "to": { "amount": 20 } } ] },
    { "at": "2026-10-17T19:39:15Z", "label": "Tint", "changes": [ { "op": "seura.whiteBalance", "from": null, "to": { "temperature": 0, "tint": 5 } } ] },
    { "at": "2026-10-17T19:40:12Z", "label": "Contrast", "changes": [ { "op": "seura.contrast", "from": { "amount": 20 }, "to": { "amount": 35 } } ] }
  ]
}
```

The hash is shortened here, and the history is too; a real file would include the earlier changes.

## Top-level fields

| Field | Required | Meaning |
| --- | --- | --- |
| `$schema` | No | URL of the JSON Schema for this version, so editors can validate the file. |
| `format` | Yes | Always `"seura-edit"`. Identifies the file type. |
| `formatVersion` | Yes | Format version as `"major.minor"`. See [Extensibility and versioning](#extensibility-and-versioning). |
| `writer` | No | The app and version that last wrote the file. Informational. |
| `modified` | No | When the file was last written, in UTC, ISO 8601. |
| `photo` | Yes | Identifies the photo. See [Photo identity](#photo-identity). |
| `operations` | No | The current edits, in render order. Absent or empty means unedited. |
| `tags` | No | The photo's tags, as strings. |
| `rating` | No | Star rating, an integer from 0 to 5. Absent means 0. |
| `history` | No | Recent changes, oldest first, for undo and redo. |
| `extensions` | No | Namespaced data that isn't an image operation, such as a plugin's own records. |

## Photo identity

The `photo` object ties the edit file to its photo and lets readers detect when the two have been separated or the photo has changed.

- **`file`** (required): the photo's file name, without a path.
- **`sha256`** (required): a SHA-256 hash of the photo file's bytes, as lowercase hex. This is the fingerprint.
- **`size`** (required): the photo file's size in bytes.
- **`width`, `height`** (required): pixel dimensions after applying the photo's own orientation metadata.

Readers use the fingerprint in two ways:

- **Reattaching.** If the named file is missing, a photo in the same folder with a matching fingerprint and no edit file of its own is the renamed original.
- **Detecting changes.** If the named file exists but its fingerprint differs, the original was modified by something else. Readers SHOULD still apply the edits and SHOULD warn the user that results may be off.

For speed, readers MAY first compare `size` and the file's modification time, and compute the hash only when those suggest a change.

## Operations

The `operations` array holds the current edits. Each entry is an object:

- **`id`** (required): the operation type. Core operations use the `seura.` prefix; all others use a reverse domain name, such as `com.example.filmGrain`.
- **`version`** (required): the version of that operation's definition, an integer starting at 1.
- **`params`** (required): the operation's settings, as defined for its type.
- **`enabled`** (optional): `false` keeps the operation in the file but skips it when rendering. Defaults to `true`.
- **`group`** (required for non-core operations): which stage it belongs to: `geometry`, `retouch`, `tone`, or `effects`. Used for render order and for copy-and-paste choices.
- **`required`** (optional, non-core only): `true` means a reader that can't render this operation MUST warn that the image will look wrong. Defaults to `false`.

**Settings, not steps.** Each operation type appears at most once. Changing a setting replaces its value; it never adds a second copy. The image therefore depends only on the final settings, never on the order the user changed them in.

**Render order.** Readers render operations in array order. Writers MUST keep the array in canonical order: the four stages below, core operations in the order shown, and non-core operations after the core ones in their stage.

| Stage | Core operations, in order |
| --- | --- |
| 1. Geometry | `seura.orient`, `seura.straighten`, `seura.crop` |
| 2. Retouch | `seura.redEye` |
| 3. Tone and color | `seura.exposure`, `seura.whiteBalance`, `seura.contrast`, `seura.saturation` |
| 4. Effects | `seura.blackAndWhite`, `seura.sepia`, `seura.vignette` |

Geometry stays in this order because each step defines the frame for the next: the crop is drawn on the rotated, straightened photo. Red-eye comes before tone and color so it works on the original colors.

**Coordinates.** Positions and sizes are fractions from 0 to 1 of the frame they refer to, so edits stay valid at any resolution. Red-eye regions are measured on the photo after its orientation metadata is applied but before any geometry operations, so they stay on the eyes when the crop changes.

**Color.** Tone and color operations work on linear-light values with Display P3 primaries, in floating point, which covers the wide color of modern phone photos. Precise transforms are defined with the reference implementation.

## Core operations

All core operations are version 1. When every setting of an operation is neutral, writers SHOULD remove the operation rather than store neutral values. The exact formulas, with reference test images, will be added as an appendix alongside the reference implementation.

| ID | Stage | Params | Meaning |
| --- | --- | --- | --- |
| `seura.orient` | Geometry | `rotate`: 0, 90, 180, or 270; `flipH`, `flipV`: true or false | Applied after the photo's own orientation metadata. Rotation is clockwise. |
| `seura.straighten` | Geometry | `angle`: −45 to 45 degrees | Rotation about the center, clockwise positive. |
| `seura.crop` | Geometry | `x`, `y`, `width`, `height`: 0 to 1; `aspect`: a ratio such as `"4:3"`, or null | A rectangle on the oriented, straightened photo. `aspect` records the user's ratio lock for editing and doesn't affect rendering. |
| `seura.redEye` | Retouch | `regions`: list of `{x, y, radius}`, 0 to 1 | Each circle darkens and desaturates red pupils inside it. Radius is a fraction of the photo's shorter side. |
| `seura.exposure` | Tone | `ev`: −4 to 4 | Brightness in photographic stops: multiplies linear light by 2^ev. |
| `seura.whiteBalance` | Tone | `temperature`, `tint`: −100 to 100 | Relative shifts from the photo as shot: temperature toward blue or amber, tint toward green or magenta. |
| `seura.contrast` | Tone | `amount`: −100 to 100 | An S-shaped curve around middle gray. |
| `seura.saturation` | Tone | `amount`: −100 to 100 | −100 removes all color. |
| `seura.blackAndWhite` | Effects | `strength`: 0 to 100 | Blends toward a luminance-only image. |
| `seura.sepia` | Effects | `strength`: 0 to 100 | Blends toward a warm brown monochrome. |
| `seura.vignette` | Effects | `amount`: −100 to 100; `size`: 0 to 100 | Negative darkens the edges, positive lightens them. Measured on the cropped frame. |

## Tags and rating

- **`tags`** is an array of distinct strings. A slash separates levels for display; each full string is a separate tag, so `family` and `family/kids` are unrelated tags. Writers MUST remove leading and trailing spaces and slashes and empty levels, and MUST NOT store two tags that differ only in letter case.
- **`rating`** is an integer from 0 to 5. Zero means unrated, and writers SHOULD omit it.

Tags and rating are kept apart from `operations` because they describe the photo rather than change how it looks; they never affect rendering.

## History

The optional `history` array records recent changes, oldest first, so undo and redo survive closing the app. It is advisory: the current state is always the `operations`, `tags`, and `rating` fields, and readers that don't offer undo can ignore history entirely.

Each record is one user action, which may change several things at once (pasting edits, applying a preset, one-click enhance):

- **`at`**: when it happened, UTC, ISO 8601.
- **`label`**: a short description for menus, such as "Contrast" or "Paste edits".
- **`changes`**: a list of changes. An operation change is `{ "op": <id>, "from": <params or null>, "to": <params or null> }`, where null means the operation was absent. A tag or rating change is `{ "field": "tags" or "rating", "from": <value>, "to": <value> }`.

Rules:

- One record per completed action. Dragging a slider produces one record when the drag ends, not one per movement.
- Writers SHOULD cap the history; Seura Photos keeps the last 50 records and drops the oldest.
- Undo applies a record's `from` values; redo applies its `to` values. Records undone and not redone are discarded when a new change is made.
- **Consistency check.** Before undoing a record, a reader MUST confirm that the current state matches that record's `to` values. If it doesn't, another app changed the file without updating the history; the reader MUST discard that record and all older ones rather than apply them.
- Writers that change the state without recording history SHOULD remove the `history` field, so stale history is never applied.

## Extensibility and versioning

The format has three ways to grow, each designed so that older readers keep working.

**New operations.** Anyone can define an operation under their own reverse domain name, with a `group` that places it in the render order. This is how plugins would add effects: a plugin supplies the operation's definition and its rendering code, and its settings live in the edit file like any core operation. The `seura.` prefix is reserved for core operations published in this spec.

**New versions of an operation.** If a core operation's math must change, it gets a new `version` rather than silently changing results. A reader renders each version as defined, so a photo edited years ago still looks the way the user left it. A reader that doesn't support an operation's version treats it as unknown.

**New format versions.** `formatVersion` is `"major.minor"`.

- A minor version only adds things: new optional fields or new core operations. Readers of an older minor version can still read the file, ignoring what they don't know.
- A major version may change existing meaning. A reader MUST NOT write a file whose major version is higher than it supports; it MAY display it, read-only, with a warning.

**Preserving the unknown.** This rule is what makes the rest work: when a reader saves a file, it MUST keep every unknown operation, field, and extension exactly as found, in place. An app that doesn't understand a plugin's effect still saves it intact, so a user can edit in two apps without one erasing the other's work.

**Unknown operations when rendering.** A reader skips operations it can't render and SHOULD tell the user the image may not match. If the operation is marked `required`, the warning MUST be prominent.

**`extensions`.** Data that isn't an image operation goes in the top-level `extensions` object, keyed by reverse domain name, such as `{ "com.example.faces": { ... } }`. Readers preserve it like any unknown field.

## Presets

A preset is an edit file that isn't tied to a photo. It uses the same format with these differences:

- File name: the preset's name plus `.seura-preset.json`. Seura Photos keeps presets in `Documents/Seura Photos/Presets`.
- `"kind": "preset"` and a `"name"` field are added.
- `photo`, `tags`, `rating`, and `history` are absent.
- `operations` normally excludes the geometry and retouch stages, since crops and red-eye belong to a single photo, but MAY include them.

Applying a preset replaces the target photo's operations in each stage the preset contains, and leaves the other stages alone. This is the same rule as pasting edits.

## Rules for readers and writers

A summary of the obligations, for implementers checking their work.

**Writers:**

- MUST write atomically: write a temporary file in the same folder, then rename it over the old one.
- MUST keep `operations` in canonical render order, with each operation type at most once.
- MUST preserve unknown operations, fields, and extensions exactly as read.
- SHOULD round numbers to at most four decimal places, so files stay readable and stable.
- SHOULD delete the edit file when the photo has no operations, tags, or rating, rather than leave an empty one.
- SHOULD update `modified` and `writer` on every write.

**Readers:**

- MUST reject files whose `format` isn't `"seura-edit"`, and MUST NOT overwrite a file they can't parse.
- MUST NOT write a file with a higher major version than they support.
- MUST render operations in array order and skip disabled ones.
- MUST run the history consistency check before undoing.
- SHOULD warn when they skip an operation they can't render, and when the photo's fingerprint doesn't match.

## Publishing

- **Specification.** This document.
- **JSON Schema.** [`schema/1.0.json`](../schema/1.0.json), JSON Schema 2020-12, to be served at the stable URL referenced by `$schema`.
- **Conformance tests.** Planned: sample photos, edit files, and expected output images, with a stated tolerance, so another implementation can verify it renders the same result.
- **Reference implementation.** Seura Photos' own rendering code, kept usable as a standalone library.
- **Licenses.** This specification under Creative Commons Attribution 4.0 ([LICENSE-SPEC](../LICENSE-SPEC)); the schema, examples, tests, and reference code under Apache 2.0 ([LICENSE](../LICENSE)).

## Decisions log

| Question | Decision |
| --- | --- |
| Format name | Keep "Seura Edit Format" for v1; it can be renamed if other apps adopt it. |
| Working color space | Linear light with Display P3 primaries, in floating point. |
| Crop frame | Defined on the straightened photo, as Lightroom does; to be confirmed by a prototype. |
| Fingerprint | Full SHA-256 of the file, computed rarely and cached. |
| Tags and rating in history | Included, so they can be undone. |
