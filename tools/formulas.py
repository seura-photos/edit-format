"""Test vectors for the formulas appendix (spec/formulas/).

    python tools/formulas.py           write tests/formulas/<operation id>.json,
                                       tests/formulas/geometry/<name>.json,
                                       and tests/reference/<name>.json
    python tools/formulas.py --check   exit 1 if any is out of date

Each operation's formula is written here in double precision, exactly as its
file in spec/formulas/ gives it, and run on a fixed set of input colors. The
geometry stage's are in geometry.py, and the reference images, which run them
all, in reference.py.
"""

import json
import sys
from pathlib import Path

import geometry
import reference

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"

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


def smoothstep(a, b, x):
    """0 at a and below, 1 at b and above, smoothly between."""
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def red_eye(color, params, size, position):
    """seura.redEye: in the circles, how red a pixel is decides how far its
    red comes down to the larger of its green and blue."""
    width, height = size
    shorter = min(width, height)
    weight = 0.0
    for region in params["regions"]:
        # A circle with no radius corrects nothing.
        if region["radius"] <= 0:
            continue
        center = (region["x"] * width, region["y"] * height)
        d = ((position[0] - center[0]) ** 2 + (position[1] - center[1]) ** 2) ** 0.5
        weight = max(weight, 1 - smoothstep(0.8, 1, d / (region["radius"] * shorter)))
    r, g, b = color
    m = max(g, b)
    if weight == 0 or r <= 0 or r <= m:
        return list(color)
    k = smoothstep(0.7, 0.9, (r - m) / r)
    return [r + (m - r) * weight * k, g, b]


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


def contrast(color, params):
    """seura.contrast: an S-curve on luminance raised to 1/2.2, around middle
    gray, with slope 2^(amount/100) there."""
    y = luminance(color)
    if y <= 0:
        return list(color)
    x = y ** (1 / 2.2)
    if x >= 1:
        return list(color)
    g = 2.0 ** (params["amount"] / 100)
    p = 0.18 ** (1 / 2.2)
    if x < p:
        curved = p * (x / p) ** g
    else:
        curved = 1 - (1 - p) * ((1 - x) / (1 - p)) ** g
    scale = curved ** 2.2 / y
    return [v * scale for v in color]


def saturation(color, params):
    """seura.saturation: each channel away from the luminance by
    1 + amount/100, with nothing clipped."""
    y = luminance(color)
    s = 1 + params["amount"] / 100
    return [y + (v - y) * s for v in color]


def tone_position(base):
    """A base as a position from black (0) to white (1), spaced roughly as
    the eye sees tones."""
    return min(max(2.0 ** base, 0.0), 1.0) ** (1 / 2.2)


def highlights(color, params, base):
    """seura.highlights: up to 2 stops at 100, weighed by x^3."""
    gain = params["amount"] / 100 * 2 * tone_position(base) ** 3
    return [v * 2.0 ** gain for v in color]


def shadows(color, params, base):
    """seura.shadows: up to 2 stops at 100, weighed by (1 - x)^3."""
    gain = params["amount"] / 100 * 2 * (1 - tone_position(base)) ** 3
    return [v * 2.0 ** gain for v in color]


def black_and_white(color, params):
    """seura.blackAndWhite: each channel toward the luminance by
    strength/100."""
    y = luminance(color)
    k = params["strength"] / 100
    return [v + (y - v) * k for v in color]


# Sepia's tone: a warm brown, scaled so its luminance is 1.
SEPIA_TONE = (1.25, 0.97, 0.56)
SEPIA = [v / luminance(SEPIA_TONE) for v in SEPIA_TONE]


def sepia(color, params):
    """seura.sepia: each channel toward the luminance in sepia's tone by
    strength/100."""
    y = luminance(color)
    k = params["strength"] / 100
    return [v + (y * tone - v) * k for v, tone in zip(color, SEPIA)]


def vignette(color, params, position):
    """seura.vignette: by how far the pixel is from the cropped frame's
    center, out to its corners, toward black (negative) or white
    (positive)."""
    d = [2 * position[0] - 1, 2 * position[1] - 1]
    r = (d[0] ** 2 + d[1] ** 2) ** 0.5
    start = 1 - params["size"] / 100
    t = min(max((r - start) / (2**0.5 - start), 0.0), 1.0)
    m = params["amount"] / 100 * t * t * (3 - 2 * t)
    if m < 0:
        return [v * (1 + m) for v in color]
    return [v + (1 - v) * m for v in color]


# The bases neighborhood operations' cases use, in stops of log2
# luminance: deep shadow, middle gray, a bright sky, and above white.
BASES = [-8, -2.5, -0.5, 0.5]

NEIGHBORHOOD_AMOUNTS = [{"amount": amount} for amount in (-100, -50, 30, 100)]

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
    "seura.contrast": (contrast, [{"amount": amount} for amount in (-100, -40, 25, 60, 100)]),
    "seura.saturation": (saturation, [{"amount": amount} for amount in (-100, -50, 30, 60, 100)]),
    "seura.blackAndWhite": (black_and_white, [{"strength": strength} for strength in (25, 60, 100)]),
    "seura.sepia": (sepia, [{"strength": strength} for strength in (25, 60, 100)]),
}

# Neighborhood operations: their formula takes the pixel's base as well,
# and each case gives it.
NEIGHBORHOOD = {
    "seura.highlights": (highlights, NEIGHBORHOOD_AMOUNTS),
    "seura.shadows": (shadows, NEIGHBORHOOD_AMOUNTS),
}


# Red-eye's inputs: the usual colors, then red pupils of several shades
# (redness 0.875 to 0.94, fully or nearly fully corrected), a reddish skin
# (0.75, a little) and a brown iris (0.625, not at all).
RED_EYE_INPUTS = INPUTS + [
    [0.5, 0.0234375, 0.03125],
    [0.25, 0.015625, 0.0234375],
    [0.75, 0.0625, 0.09375],
    [0.375, 0.046875, 0.03125],
    [0.1875, 0.046875, 0.015625],
    [0.125, 0.046875, 0.0234375],
]

# Red-eye's cases: the photo's upright size and a pixel's position in it, in
# its pixels, with the regions. One circle centered at (100, 150) with a
# radius of 15 pixels: at its center, inside its soft edge, halfway through
# the edge, and outside. Then two overlapping circles, where the larger
# weight counts, not their sum.
ONE = {"regions": [{"x": 0.25, "y": 0.5, "radius": 0.05}]}
TWO = {"regions": [{"x": 0.25, "y": 0.5, "radius": 0.05}, {"x": 0.27, "y": 0.5, "radius": 0.05}]}
# A circle with no radius, over the first: it changes nothing.
EMPTY = {"regions": [{"x": 0.25, "y": 0.5, "radius": 0}]}
RED_EYE_CASES = [
    (ONE, [100, 150]),
    (ONE, [110, 150]),
    (ONE, [113.5, 150]),
    (ONE, [116, 150]),
    (TWO, [104, 150]),
    (TWO, [120, 150]),
    (TWO, [121.5, 150]),
    (EMPTY, [100, 150]),
]
RED_EYE_SIZE = [400, 300]

# Operations measured on the cropped frame: their formula takes the
# pixel's position as well, as fractions of the frame from its top left
# corner, and each case gives it.
POSITIONAL = {
    "seura.vignette": (
        vignette,
        [
            {"amount": amount, "size": size}
            for amount, size in ((-100, 0), (-25, 60), (40, 30), (100, 100))
        ],
    ),
}

# The positions their cases use: the center, toward an edge, past where a
# small vignette starts, and near a corner.
POSITIONS = [[0.5, 0.5], [0.8125, 0.5], [0.125, 0.875], [0.984375, 0.015625]]


def rounded(color):
    return [float(f"{v:.9g}") for v in color]


def build(operation):
    if operation in NEIGHBORHOOD:
        formula, cases = NEIGHBORHOOD[operation]
        cases = [
            {"params": params, "base": base, "input": color, "output": rounded(formula(color, params, base))}
            for params in cases
            for base in BASES
            for color in INPUTS
        ]
    elif operation == "seura.redEye":
        cases = [
            {
                "params": params,
                "size": RED_EYE_SIZE,
                "position": position,
                "input": color,
                "output": rounded(red_eye(color, params, RED_EYE_SIZE, position)),
            }
            for params, position in RED_EYE_CASES
            for color in RED_EYE_INPUTS
        ]
    elif operation in POSITIONAL:
        formula, cases = POSITIONAL[operation]
        cases = [
            {"params": params, "position": position, "input": color, "output": rounded(formula(color, params, position))}
            for params in cases
            for position in POSITIONS
            for color in INPUTS
        ]
    else:
        formula, cases = OPERATIONS[operation]
        cases = [
            {"params": params, "input": color, "output": rounded(formula(color, params))}
            for params in cases
            for color in INPUTS
        ]
    return {"operation": operation, "version": 1, "tolerance": TOLERANCE, "cases": cases}


def text(operation):
    """The vector file: one case to a line, so a change reads well in a diff."""
    vectors = build(operation)
    head = json.dumps({key: value for key, value in vectors.items() if key != "cases"}, indent=2)
    cases = ",\n".join(f"    {json.dumps(case)}" for case in vectors["cases"])
    return head[:-2] + ',\n  "cases": [\n' + cases + "\n  ]\n}\n"


def geometry_text(name):
    """A geometry vector file: each case, and each row of the sampling
    image, on a line of its own."""
    vectors = geometry.build(name)
    lists = [key for key in ("image", "cases") if key in vectors]
    head = json.dumps({key: value for key, value in vectors.items() if key not in lists}, indent=2)
    body = ",\n".join(
        f'  "{key}": [\n' + ",\n".join(f"    {json.dumps(item)}" for item in vectors[key]) + "\n  ]"
        for key in lists
    )
    return head[:-2] + ",\n" + body + "\n}\n"


def files():
    """Every generated file's path under tests/, and what makes its text."""
    made = {
        f"formulas/{operation}.json": (text, operation)
        for operation in ["seura.redEye", *OPERATIONS, *NEIGHBORHOOD, *POSITIONAL]
    }
    made.update({f"formulas/geometry/{name}.json": (geometry_text, name) for name in geometry.FILES})
    made.update({f"reference/{path}": (lambda make: make(), make) for path, make in reference.files().items()})
    return made


def stale():
    """The generated files that don't match the formulas, or are missing,
    by their path under tests/ without .json."""
    return [
        path.removesuffix(".json")
        for path, (make, name) in files().items()
        if not (TESTS / path).exists() or (TESTS / path).read_text(encoding="utf-8") != make(name)
    ]


def main(argv):
    if argv == ["--check"]:
        out_of_date = stale()
        for path in out_of_date:
            print(f"FAIL tests/{path}.json is out of date; run tools/formulas.py")
        return 1 if out_of_date else 0
    for path, (make, name) in files().items():
        (TESTS / path).parent.mkdir(parents=True, exist_ok=True)
        (TESTS / path).write_text(make(name), encoding="utf-8", newline="\n")
        print(f"wrote tests/{path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
