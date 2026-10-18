#!/usr/bin/env python3
"""Validate Seura edit files against the schema plus the rules JSON Schema can't express.

Usage:
    python tools/check.py FILE...        validate the given files
    python tools/check.py --self-test    validate examples/ (must pass) and tests/invalid/ (must fail)

Requires: pip install jsonschema
"""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "1.0.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())

STAGES = ["geometry", "retouch", "tone", "effects"]
CORE_ORDER = [
    ("seura.orient", "geometry"),
    ("seura.straighten", "geometry"),
    ("seura.crop", "geometry"),
    ("seura.redEye", "retouch"),
    ("seura.exposure", "tone"),
    ("seura.whiteBalance", "tone"),
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

    return errors


def check_file(path):
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"cannot read JSON: {exc}"]
    errors = [
        f"{'/'.join(str(p) for p in e.absolute_path) or '(root)'}: {e.message}"
        for e in sorted(VALIDATOR.iter_errors(doc), key=lambda e: list(e.absolute_path))
    ]
    return errors + rule_errors(doc)


def self_test():
    failed = False
    for path in sorted((ROOT / "examples").glob("*.json")):
        errors = check_file(path)
        status = "ok" if not errors else "FAIL (expected valid)"
        failed |= bool(errors)
        print(f"{status:24} examples/{path.name}")
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
