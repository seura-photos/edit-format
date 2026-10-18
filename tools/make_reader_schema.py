#!/usr/bin/env python3
"""Derive schema/1.x-reader.json from schema/1.0.json.

Usage:
    python tools/make_reader_schema.py

The reader schema is generated, never edited by hand: change 1.0.json, then run this.
check.py --self-test fails if the reader schema is out of date.

What changes from 1.0.json (see the spec's "Reading a newer minor version"):
- formatVersion accepts any 1.x version;
- unknown fields are accepted everywhere, except inside the parameters of known operation versions;
- unknown core operation ids are accepted (they are treated as unknown operations);
- unknown kinds of history change are accepted (such records fail the consistency check).
"""

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "schema" / "1.0.json"
TARGET = ROOT / "schema" / "1.x-reader.json"


def _allow_unknown_fields(node):
    if isinstance(node, dict):
        if node.get("additionalProperties") is False:
            del node["additionalProperties"]
        for value in node.values():
            _allow_unknown_fields(value)
    elif isinstance(node, list):
        for value in node:
            _allow_unknown_fields(value)


def build():
    schema = copy.deepcopy(json.loads(SOURCE.read_text(encoding="utf-8")))

    schema.pop("additionalProperties", None)
    for value in schema["properties"].values():
        _allow_unknown_fields(value)
    for name, definition in schema["$defs"].items():
        if not name.startswith("op"):  # parameters of known operation versions stay exact
            _allow_unknown_fields(definition)

    schema["$id"] = "https://seuraphotos.app/schema/edit/1.x-reader.json"
    schema["title"] = "Seura Edit Format 1.x, reader schema"
    schema["description"] = (
        "For a 1.0 reader validating a file with a higher 1.x minor version. Checks every field format 1.0 "
        "defines, and accepts fields, core operations, and history change types it doesn't know. "
        "Generated from 1.0.json by tools/make_reader_schema.py."
    )
    schema["properties"]["formatVersion"] = {"type": "string", "pattern": "^1\\.(0|[1-9][0-9]*)$"}

    core = schema["$defs"]["operation"]["then"]
    core["description"] = (
        "Core operation: known ids have their parameters checked; unknown core ids are accepted "
        "and treated as unknown operations."
    )
    core["properties"].pop("id", None)
    if not core["properties"]:
        del core["properties"]

    items = schema["$defs"]["historyRecord"]["properties"]["changes"]["items"]
    items["anyOf"] = items.pop("oneOf") + [
        {
            "description": "A kind of change from a later minor version: accepted, but the record "
            "fails the consistency check.",
            "type": "object",
            "not": {
                "anyOf": [
                    {"required": ["op"]},
                    {"required": ["field"], "properties": {"field": {"enum": ["tags", "rating"]}}},
                ]
            },
        }
    ]
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    TARGET.write_text(build(), encoding="utf-8")
    print(f"wrote {TARGET.relative_to(ROOT)}")
