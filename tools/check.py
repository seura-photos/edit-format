#!/usr/bin/env python3
"""Validate Seura edit files against the schema plus the rules JSON Schema can't express.

Usage:
    python tools/check.py FILE...        validate the given files
    python tools/check.py --self-test    validate examples/ and tests/valid/ (must pass) and tests/invalid/ (must fail),
                                         and confirm schema/1.x-reader.json is up to date

Files whose formatVersion is exactly "1.0" are checked against schema/1.0.json; files with a higher
1.x minor version against schema/1.x-reader.json (see the spec's "Reading a newer minor version").

Requires: pip install jsonschema
"""

import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import make_reader_schema  # noqa: E402

SUPPORTED_MINOR = 0  # this checker implements format 1.0


def _validator(name):
    schema = json.loads((ROOT / "schema" / name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


STRICT = _validator("1.0.json")
READER = _validator("1.x-reader.json")
VERSION = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

STAGES = ["geometry", "retouch", "tone", "effects"]
CORE_ORDER = [
    ("seura.orient", "geometry"),
    ("seura.straighten", "geometry"),
    ("seura.crop", "geometry"),
    ("seura.redEye", "retouch"),
    ("seura.exposure", "tone"),
    ("seura.whiteBalance", "tone"),
    ("seura.highlights", "tone"),
    ("seura.shadows", "tone"),
    ("seura.contrast", "tone"),
    ("seura.saturation", "tone"),
    ("seura.blackAndWhite", "effects"),
    ("seura.sepia", "effects"),
    ("seura.vignette", "effects"),
]
CORE_RANK = {op_id: i for i, (op_id, _) in enumerate(CORE_ORDER)}
CORE_STAGE = dict(CORE_ORDER)


def rule_errors(doc):
    """Checks the spec requires but the schema can't express."""
    errors = []
    ops = doc.get("operations", [])
    if not isinstance(ops, list):
        return errors

    ids = [op.get("id") for op in ops if isinstance(op, dict)]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        errors.append(f"operation types appear more than once: {', '.join(duplicates)}")

    # Canonical order: by stage; core operations in fixed order and before non-core within a stage.
    def sort_key(op):
        op_id = op.get("id", "")
        if op_id in CORE_RANK:
            return (STAGES.index(CORE_STAGE[op_id]), 0, CORE_RANK[op_id])
        stage = op.get("group")
        return (STAGES.index(stage) if stage in STAGES else len(STAGES), 1, 0)

    keys = [sort_key(op) for op in ops if isinstance(op, dict)]
    for position, (earlier, later) in enumerate(zip(keys, keys[1:]), start=1):
        if later < earlier:
            errors.append(f"operations are not in canonical render order (item {position + 1})")
            break

    tags = doc.get("tags", [])
    if isinstance(tags, list):
        lowered = [t.lower() for t in tags if isinstance(t, str)]
        clashes = sorted({t for t in lowered if lowered.count(t) > 1})
        if clashes:
            errors.append(f"tags differ only in letter case: {', '.join(clashes)}")

    history = doc.get("history", [])
    if isinstance(history, list):
        flags = [isinstance(r, dict) and r.get("undone") is True for r in history]
        if any(flags) and flags != sorted(flags):
            errors.append("undone history records must all come after the records that aren't undone")

    return errors


def pick_validator(doc):
    """Returns (validator, error) for the document's formatVersion."""
    version = doc.get("formatVersion") if isinstance(doc, dict) else None
    match = VERSION.match(version) if isinstance(version, str) else None
    if not match:
        return STRICT, None  # the strict schema reports the bad value
    major, minor = int(match.group(1)), int(match.group(2))
    if major != 1:
        return None, f"formatVersion {version}: major version {major} is not supported (read-only at most)"
    return (STRICT if minor <= SUPPORTED_MINOR else READER), None


def check_file(path):
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"cannot read JSON: {exc}"]
    validator, error = pick_validator(doc)
    if error:
        return [error]
    errors = [
        f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
        for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path))
    ]
    return errors + rule_errors(doc)


def self_test():
    failed = False
    current = (ROOT / "schema" / "1.x-reader.json").read_text(encoding="utf-8")
    if current != make_reader_schema.build():
        failed = True
        print("FAIL                     schema/1.x-reader.json is out of date; run tools/make_reader_schema.py")
    else:
        print("ok                       schema/1.x-reader.json is up to date")
    valid = sorted((ROOT / "examples").glob("*.json")) + sorted((ROOT / "tests" / "valid").glob("*.json"))
    for path in valid:
        errors = check_file(path)
        status = "ok" if not errors else "FAIL (expected valid)"
        failed |= bool(errors)
        print(f"{status:24} {path.relative_to(ROOT).as_posix()}")
        for e in errors:
            print(f"    {e}")
    for path in sorted((ROOT / "tests" / "invalid").glob("*.json")):
        errors = check_file(path)
        status = "ok (rejected)" if errors else "FAIL (expected invalid)"
        failed |= not errors
        print(f"{status:24} tests/invalid/{path.name}")
    return 1 if failed else 0


def main(argv):
    if argv == ["--self-test"]:
        return self_test()
    if not argv:
        print(__doc__)
        return 2
    exit_code = 0
    for path in argv:
        errors = check_file(path)
        print(f"{'ok' if not errors else 'INVALID':8} {path}")
        for e in errors:
            print(f"    {e}")
        exit_code |= bool(errors)
    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
