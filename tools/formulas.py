"""Test vectors for the formulas appendix (spec/formulas/).

    python tools/formulas.py           write tests/formulas/<operation id>.json
    python tools/formulas.py --check   exit 1 if any is out of date

Each operation's formula is written here in double precision, exactly as its
file in spec/formulas/ gives it, and run on a fixed set of input colors.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VECTORS = ROOT / "tests" / "formulas"

# spec/formulas/README.md, "Test vectors".
TOLERANCE = {"absolute": 0.0001, "relative": 0.001}

# Linear Display P3 colors that half-precision floats hold exactly: black,
# grays from deep shadow to above white, and colors toward each primary and
# between them.
INPUTS = [
    [0.0, 0.0, 0.0],
    [0.0625, 0.0625, 0.0625],
    [0.1875, 0.1875, 0.1875],
    [0.5, 0.5, 0.5],
    [1.0, 1.0, 1.0],
    [1.5, 1.5, 1.5],
    [0.75, 0.25, 0.125],
    [0.125, 0.625, 0.25],
    [0.25, 0.375, 0.875],
    [0.9375, 0.875, 0.0625],
    [0.03125, 0.015625, 0.0078125],
]


def exposure(color, params):
    """seura.exposure: every channel times 2^ev."""
    scale = 2.0 ** params["ev"]
    return [v * scale for v in color]


# spec/formulas/README.md, "Luminance".
LUMINANCE = (0.2289746, 0.6917385, 0.0792869)


def luminance(color):
    return sum(weight * v for weight, v in zip(LUMINANCE, color))


def white_balance(color, params):
    """seura.whiteBalance: a gain on each channel, scaled so gray keeps its
    luminance."""
    t = params["temperature"] / 100
    n = params["tint"] / 100
    gains = [2.0 ** (t / 2), 2.0 ** (-n / 2), 2.0 ** (-t / 2)]
    k = luminance(gains)
    return [v * g / k for v, g in zip(color, gains)]


# Each operation: its formula, and the params its vectors use.
OPERATIONS = {
    "seura.exposure": (exposure, [{"ev": ev} for ev in (-4, -1.5, 0.3, 1, 4)]),
    "seura.whiteBalance": (
        white_balance,
        [
            {"temperature": temperature, "tint": tint}
            for temperature, tint in ((-100, 0), (100, 0), (0, -100), (0, 100), (35, -20), (-60, 45))
        ],
    ),
}


def build(operation):
    formula, cases = OPERATIONS[operation]
    return {
        "operation": operation,
        "version": 1,
        "tolerance": TOLERANCE,
        "cases": [
            {
                "params": params,
                "input": color,
                "output": [float(f"{v:.9g}") for v in formula(color, params)],
            }
            for params in cases
            for color in INPUTS
        ],
    }


def text(operation):
    """The vector file: one case to a line, so a change reads well in a diff."""
    vectors = build(operation)
    head = json.dumps({key: value for key, value in vectors.items() if key != "cases"}, indent=2)
    cases = ",\n".join(f"    {json.dumps(case)}" for case in vectors["cases"])
    return head[:-2] + ',\n  "cases": [\n' + cases + "\n  ]\n}\n"


def stale():
    """The vector files that don't match the formulas, or are missing."""
    return [
        operation
        for operation in OPERATIONS
        if not (VECTORS / f"{operation}.json").exists()
        or (VECTORS / f"{operation}.json").read_text(encoding="utf-8") != text(operation)
    ]


def main(argv):
    if argv == ["--check"]:
        out_of_date = stale()
        for operation in out_of_date:
            print(f"FAIL tests/formulas/{operation}.json is out of date; run tools/formulas.py")
        return 1 if out_of_date else 0
    VECTORS.mkdir(parents=True, exist_ok=True)
    for operation in OPERATIONS:
        (VECTORS / f"{operation}.json").write_text(text(operation), encoding="utf-8", newline="\n")
        print(f"wrote tests/formulas/{operation}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
