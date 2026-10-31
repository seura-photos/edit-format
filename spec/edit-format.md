# Seura Edit Format, version 1.0

Status: draft · Last updated: 2026-10-18

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
- **`size`** (required): the photo file's size in bytes.
- **`sha256`** (optional): a SHA-256 hash of the photo file's bytes, as lowercase hex. This is the fingerprint.
- **`width`, `height`** (optional, both or neither): pixel dimensions after applying the photo's own orientation metadata.

The fingerprint and dimensions need the photo's contents. A photo in a cloud-synced folder may exist only in the cloud until something reads it, and reading it downloads the whole file, so a writer may create an edit file (say, to tag or rate a photo) without them. A writer that reads the photo later SHOULD fill them in. A writer MUST NOT store a guessed or placeholder value: a field is either correct or absent.

Readers use the fingerprint in two ways:

- **Reattaching.** If the named file is missing, a photo in the same folder with a matching fingerprint and no edit file of its own is the renamed original. Without a fingerprint, an edit file belongs to its photo by name only, and a renamed photo can't be matched back to it.
- **Detecting changes.** If the named file exists but its fingerprint differs, the original was modified by something else. Readers SHOULD still apply the edits and SHOULD warn the user that results may be off. Without a fingerprint, a reader MAY compare `size` instead, which catches most changes but not all.

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
| 3. Tone and color | `seura.exposure`, `seura.whiteBalance`, `seura.highlights`, `seura.shadows`, `seura.contrast`, `seura.saturation` |
| 4. Effects | `seura.blackAndWhite`, `seura.sepia`, `seura.vignette` |

Geometry stays in this order because each step defines the frame for the next: the crop is drawn on the rotated, straightened photo.

**Geometry frame and sampling.** The *oriented photo* is the photo with its orientation metadata and `seura.orient` applied: W × H pixels. Straightening turns the photo about the oriented photo's center, in pixels, so its shape isn't distorted, but doesn't change the frame: the crop is always a rectangle in the oriented photo's W × H frame, and its fractions keep their meaning at any angle. The crop's edges are rounded to whole pixels of that frame: left = round(x × W), top = round(y × H), and the output is round(width × W) × round(height × H) pixels. Geometry is a coordinate transform: the center of each output pixel is mapped back through the crop, the turn, and the orientation to a position in the photo as decoded, and the photo is sampled there with Catmull-Rom bicubic interpolation, as the [formulas appendix](formulas/README.md) defines. Catmull-Rom returns a pixel unchanged when the position falls on its center, so without straightening, geometry copies whole pixels exactly. Positions past the photo's edge, such as the corners a turned photo leaves uncovered, take the nearest edge pixel. Writers SHOULD keep the crop inside the turned photo so no such corners show; Seura Photos always does. A file with an angle and no crop is drawn as written. These rules define the full-resolution result; how an app scales it for the screen is up to the app. Red-eye comes before tone and color so it works on the original colors. Highlights and shadows come after exposure and white balance, so they work on the corrected brightness and color, and before contrast, which shapes the overall result.

**Coordinates.** Positions and sizes are fractions from 0 to 1 of the frame they refer to, so edits stay valid at any resolution. Red-eye regions are measured on the photo after its orientation metadata is applied but before any geometry operations, so they stay on the eyes when the crop changes.

**Color.** Tone and color operations work on linear-light values with Display P3 primaries, in floating point, which covers the wide color of modern phone photos. The exact formulas are in the [formulas appendix](formulas/README.md).

**Decoding into the working space.** The format starts from the photo in the working space; how a reader gets it there is its own, but two readers that decode differently draw the same file differently. So readers SHOULD:

- apply the photo's orientation metadata, giving the upright photo that red-eye regions and the luminance guide are measured on;
- convert colors with the photo's own color information: its embedded ICC profile, or the color description a format carries instead (such as HEIC's or PNG's), and sRGB when there's none;
- convert in floating point without clipping, so colors outside Display P3 keep components below 0 or above 1, as the appendix expects;
- for a photo with an HDR gain map, render its standard (SDR) image in format 1.0. A later minor version may say how gain maps take part.

## Core operations

All core operations are version 1. When every setting of an operation is neutral, writers SHOULD remove the operation rather than store neutral values. The exact formulas, with test vectors, are in the [formulas appendix](formulas/README.md), added one operation at a time alongside the reference implementation.

| ID | Stage | Params | Meaning |
| --- | --- | --- | --- |
| `seura.orient` | Geometry | `rotate`: 0, 90, 180, or 270; `flipH`, `flipV`: true or false | Applied after the photo's own orientation metadata. The photo is turned first, clockwise, then flipped as the turned photo is seen: `flipH` mirrors left to right, `flipV` top to bottom. Both flips together equal a half turn; writers SHOULD store that as `rotate` 180 more with both flips false, and readers MUST accept either. |
| `seura.straighten` | Geometry | `angle`: −45 to 45 degrees | Rotation about the oriented photo's center, clockwise positive as seen on screen. The frame doesn't change (above). |
| `seura.crop` | Geometry | `x`, `y`, `width`, `height`: 0 to 1; `aspect`: a ratio such as `"4:3"`, or null | A rectangle in the oriented photo's frame, over the straightened photo (above). `aspect` records the user's ratio lock for editing and doesn't affect rendering. |
| `seura.redEye` | Retouch | `regions`: list of `{x, y, radius}`, 0 to 1 | Each circle darkens and desaturates red pupils inside it. At most 64 regions, so every reader can draw every valid file in one pass; no real photo needs more. Radius is a fraction of the photo's shorter side. |
| `seura.exposure` | Tone | `ev`: −4 to 4 | Brightness in photographic stops: multiplies linear light by 2^ev. Apps may label it "Brightness"; Seura Photos does. |
| `seura.whiteBalance` | Tone | `temperature`, `tint`: −100 to 100 | Relative shifts from the photo as shot: temperature toward blue or amber, tint toward green or magenta. |
| `seura.highlights` | Tone | `amount`: −100 to 100 | Adjusts the bright areas of the photo, with little effect on dark ones. Negative recovers detail in bright areas such as skies; positive brightens them. A neighborhood operation (below). |
| `seura.shadows` | Tone | `amount`: −100 to 100 | Adjusts the dark areas, with little effect on bright ones. Positive lifts detail out of shadows, such as a backlit face; negative deepens them. A neighborhood operation (below). |
| `seura.contrast` | Tone | `amount`: −100 to 100 | An S-shaped curve around middle gray. |
| `seura.saturation` | Tone | `amount`: −100 to 100 | −100 removes all color. |
| `seura.blackAndWhite` | Effects | `strength`: 0 to 100 | Blends toward a luminance-only image. |
| `seura.sepia` | Effects | `strength`: 0 to 100 | Blends toward a warm brown monochrome. |
| `seura.vignette` | Effects | `amount`: −100 to 100; `size`: 0 to 100 | Negative darkens the edges, positive lightens them. Measured on the cropped frame. |

**Neighborhood operations.** Most operations change each pixel based on that pixel alone. `seura.highlights` and `seura.shadows` also depend on the brightness of the area around each pixel, so that a bright sky can be darkened without flattening the clouds in it, and a face lifted without graying the black of a jacket beside it. The size of that area is defined as a fraction of the photo's dimensions, never in pixels, so a preview rendered at screen resolution matches the full-resolution export. The exact method, its radius, and its edge handling are part of the formulas appendix.

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
- **`undone`**: `true` if the record has been undone and not redone. Absent otherwise. Undone records are always the last records in the array, so redo works after the app is closed and reopened.

Rules:

- One record per completed action. Dragging a slider produces one record when the drag ends, not one per movement.
- Writers SHOULD cap the history; Seura Photos keeps the last 50 records and drops the oldest.
- **Undo** applies the `from` values of the last record that isn't undone, and marks it `"undone": true`.
- **Redo** applies the `to` values of the first undone record, and removes its `undone` flag.
- **A new change** discards every undone record, then appends its own record. Undone records count toward the cap.
- **Consistency check.** Before undoing a record, a reader MUST confirm that the current state matches that record's `to` values; before redoing one, that it matches the record's `from` values. If it doesn't, another app changed the file without updating the history. On a failed undo check, the reader MUST discard that record and all older ones; on a failed redo check, it MUST discard all undone records. It never applies a record that fails the check.
- A reader that finds a change it doesn't understand in a record (for example, a change type added in a later minor version) MUST treat that record as failing the consistency check.
- Writers that change the state without recording history SHOULD remove the `history` field, so stale history is never applied.

## Extensibility and versioning

The format has three ways to grow, each designed so that older readers keep working.

**New operations.** Anyone can define an operation under their own reverse domain name, with a `group` that places it in the render order. This is how plugins would add effects: a plugin supplies the operation's definition and its rendering code, and its settings live in the edit file like any core operation. The `seura.` prefix is reserved for core operations published in this spec.

**New versions of an operation.** If a core operation's math must change, it gets a new `version` rather than silently changing results. A reader renders each version as defined, so a photo edited years ago still looks the way the user left it. A reader that doesn't support an operation's version treats it as unknown.

**New format versions.** `formatVersion` is `"major.minor"`.

- A minor version only adds things: new optional fields, new core operations, or new kinds of history change. Readers of an older minor version can still read the file, ignoring what they don't know.
- A major version may change existing meaning. A reader MUST NOT write a file whose major version is higher than it supports; it MAY display it, read-only, with a warning.

**Reading a newer minor version.** The schema for a version describes that version exactly, so `schema/1.0.json` rejects a 1.1 file's new fields. A 1.0 reader handling a file with a higher minor version, such as `"1.1"`:

- validates it against the reader schema, [`schema/1.x-reader.json`](../schema/1.x-reader.json), which checks every field 1.0 defines but accepts fields, core operations, and history change types it doesn't know;
- applies the 1.0 rules to everything it recognizes, and treats an unknown core operation like any other unknown operation (skipped when rendering, kept when saving);
- when it saves the file, keeps `formatVersion` as it found it and preserves everything it doesn't understand, as for any unknown content.

A file whose `formatVersion` is exactly a version the reader supports is validated against that version's own schema.

**Preserving the unknown.** This rule is what makes the rest work: when a reader saves a file, it MUST keep every unknown operation, field, and extension exactly as found, in place. An app that doesn't understand a plugin's effect still saves it intact, so a user can edit in two apps without one erasing the other's work.

**Unknown operations when rendering.** A reader skips operations it can't render and SHOULD tell the user the image may not match. If the operation is marked `required`, the warning MUST be prominent.

**`extensions`.** Data that isn't an image operation goes in the top-level `extensions` object, keyed by reverse domain name, such as `{ "com.example.faces": { ... } }`. Readers preserve it like any unknown field.

## Presets

A preset is an edit file that isn't tied to a photo. It uses the same format with these differences:

- File name: the preset's name plus `.seura-preset.json`. Seura Photos keeps presets in a `Seura Photos/Presets` folder in the user's home folder.
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
- SHOULD fill in a missing `sha256`, `width`, and `height` when they read the photo, and MUST NOT store guessed values.
- SHOULD delete the edit file when the photo has no operations, tags, or rating, rather than leave an empty one.
- SHOULD update `modified` and `writer` on every write.

**Readers:**

- MUST reject files whose `format` isn't `"seura-edit"`, and MUST NOT overwrite a file they can't parse.
- MUST NOT write a file with a higher major version than they support.
- MUST render operations in array order and skip disabled ones.
- MUST run the history consistency check before undoing or redoing.
- MUST validate a file with a higher minor version against the reader schema, not reject it, and MUST NOT lower its `formatVersion` when saving.
- SHOULD warn when they skip an operation they can't render, and when the photo's fingerprint doesn't match.

## Publishing

- **Specification.** This document.
- **JSON Schema.** [`schema/1.0.json`](../schema/1.0.json), JSON Schema 2020-12, served at the stable URL referenced by `$schema`. The reader schema for files with a higher 1.x minor version is [`schema/1.x-reader.json`](../schema/1.x-reader.json).
- **Conformance tests.** Planned: sample photos, edit files, and expected output images, with a stated tolerance, so another implementation can verify it renders the same result.
- **Reference implementation.** Seura Photos' own rendering code, kept usable as a standalone library.
- **Licenses.** This specification under Creative Commons Attribution 4.0 ([LICENSE-SPEC](../LICENSE-SPEC)); the schema, examples, tests, and reference code under Apache 2.0 ([LICENSE](../LICENSE)).

## Decisions log

| Question | Decision |
| --- | --- |
| Format name | Keep "Seura Edit Format" for v1; it can be renamed if other apps adopt it. |
| Working color space | Linear light with Display P3 primaries, in floating point. |
| Crop frame | The oriented photo's own W × H rectangle, which straightening doesn't change, so a crop keeps its meaning at any angle and can grow back as the angle returns to zero. Uncovered corners take the nearest edge pixel. Rejected: the box around the turned photo (its fractions change with every angle) and the largest rectangle inside it (every angle change moves every crop). Proposed by Claude Code while building M4; decided in the design session, 2026-10-29. |
| Decoding into the working space | Recommended (SHOULD), not required: the reference images start from the working space, so conformance doesn't depend on decoding, and decoders differ by platform. Gain maps are left to a later minor version. Raised by Claude Code before 1.0; decided in the design session, 2026-10-30. |
| Red-eye regions | At most 64 per photo: a group photo of 30 faces has 60 eyes, and a fixed limit lets every reader, including a GPU with a fixed-size uniform block, draw every valid file. Raised by Claude Code while building M4; decided in the design session, 2026-10-30. |
| Order within `seura.orient` | Turn, then flip as seen, so a flip pressed after a turn mirrors what's on screen. (A flip followed by a quarter turn equals the quarter turn followed by the other flip, which is how an app records a turn pressed after a flip.) Proposed by Claude Code while building M4; decided in the design session, 2026-10-29. |
| Sampling | Catmull-Rom bicubic, defined for the full-resolution result: sharper than bilinear for straightened photos, and exact for whole-pixel moves. |
| Highlights and shadows guide | Built from the photo before any geometry, and looked up at each pixel's position in it, so rotation, straightening and crop never change it and no uncovered corners enter it. |
| Fingerprint | Full SHA-256 of the file, computed rarely and cached. |
| Tags and rating in history | Included, so they can be undone. |
| Redo across sessions | Undone records stay in the history, marked `"undone": true`, until a new change discards them. Found missing while implementing Seura Photos' edit file library. |
| Photo fingerprint and dimensions | Optional, filled in when the photo is first read, so a cloud-only photo can be tagged or rated without downloading it. Raised by Nevada while designing support for cloud-synced folders. |
| Highlights and shadows | Added to version 1.0 before release, as `seura.highlights` and `seura.shadows` in the tone stage. Suggested by a friend of the project; Picasa had both. `seura.exposure` keeps its name, since its value is in photographic stops; apps label the slider as they like. |
| Files from a newer minor version | Validated against a separate reader schema that checks known fields and accepts unknown ones; `formatVersion` is never lowered on save. Found missing while implementing Seura Photos' edit file library. |
