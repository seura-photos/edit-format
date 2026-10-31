"""Reference images for the formulas appendix (spec/formulas/reference-images.md),
written to tests/reference/ by tools/formulas.py.

A small photo, made here, is rendered with each case's operations through
the whole pipeline, in double precision, exactly as the appendix gives it:
geometry, then red-eye, then tone and color with the luminance guide, then
the effects. Each formula is the one in formulas.py or geometry.py; only the
guide and the order they run in are new here.
"""

import json
import math
import struct

import formulas
import geometry

# spec/formulas/README.md, "Test vectors".
TOLERANCE = {"absolute": 0.0001, "relative": 0.001}

# The photo's size: small enough to keep the files small, and under the
# guide's 1024 pixels, so the guide is built on the photo itself and no
# downscaling filter is involved.
WIDTH, HEIGHT = 64, 48


def half(value):
    """The nearest value a half-precision float holds."""
    return struct.unpack("<e", struct.pack("<e", value))[0]


def photo_pixel(x, y):
    """The photo's pixel at column x, row y: a sky with a sun brighter than
    white, a dark tree against it, the ground, a face with two red pupils,
    and a row of colors along the bottom, one of them outside Display P3.
    A little texture everywhere gives the guide something to smooth."""
    texture = ((x * 7 + y * 13) % 5 - 2) / 64
    if y >= 44:
        bars = [
            [0.75, 0.0625, 0.0625],
            [0.875, 0.5, 0.0625],
            [0.6875, 0.75, 0.125],
            [0.125, 0.5625, 0.1875],
            [0.0625, 0.375, 0.6875],
            [0.3125, 0.125, 0.75],
            [0.625, 0.125, 0.5],
            [0.5, -0.0234375, 0.0625],
        ]
        return bars[x // 8]
    if (x - 40) ** 2 + (y - 34) ** 2 <= 49:
        if (x - 37) ** 2 + (y - 33) ** 2 <= 2 or (x - 43) ** 2 + (y - 33) ** 2 <= 2:
            return [0.4375, 0.03125, 0.0390625]
        return [0.5 + texture / 4, 0.3125, 0.21875]
    if 10 <= x <= 17 and 8 <= y <= 30:
        return [0.03125, 0.046875 + texture / 8, 0.0234375]
    if y < 26:
        if (x - 52) ** 2 + (y - 6) ** 2 <= 12:
            return [1.5, 1.4375, 1.25]
        t = y / 25
        return [0.375 + 0.375 * t + texture, 0.5 + 0.3125 * t + texture, 0.875 + 0.125 * t + texture]
    t = (y - 26) / 17
    return [0.09375 - 0.0625 * t + texture / 4, 0.0703125 - 0.046875 * t + texture / 4, 0.046875 - 0.03125 * t]


def photo():
    """The photo, upright, as rows of linear Display P3 colors that
    half-precision floats hold exactly."""
    return [[[half(v) for v in photo_pixel(x, y)] for x in range(WIDTH)] for y in range(HEIGHT)]


# The luminance guide (luminance-guide.md).

GUIDE_SIZE = 1024
GUIDE_EPSILON = 0.1


def log_luminance(color):
    return math.log2(max(formulas.luminance(color), 2.0**-12))


def box_mean(values, r):
    """The mean over the (2r + 1) × (2r + 1) square around each value, past
    the edge repeating the nearest edge value: a mean across, then down."""
    height, width = len(values), len(values[0])
    count = 2 * r + 1
    across = [
        [sum(row[min(max(i + k, 0), width - 1)] for k in range(-r, r + 1)) / count for i in range(width)]
        for row in values
    ]
    return [
        [sum(across[min(max(j + k, 0), height - 1)][i] for k in range(-r, r + 1)) / count for i in range(width)]
        for j in range(height)
    ]


def guide(image, white_balance):
    """The guide's A and B for an upright photo no larger than the guide's
    size, which is then the guide image itself."""
    height, width = len(image), len(image[0])
    assert max(width, height) <= GUIDE_SIZE
    r = max(1, geometry.round_half_up(0.02 * max(width, height)))
    l = [[log_luminance(formulas.white_balance(color, white_balance)) for color in row] for row in image]
    m = box_mean(l, r)
    squares = box_mean([[v * v for v in row] for row in l], r)
    a = [[0.0] * width for _ in range(height)]
    b = [[0.0] * width for _ in range(height)]
    for j in range(height):
        for i in range(width):
            v = max(squares[j][i] - m[j][i] ** 2, 0.0)
            a[j][i] = v / (v + GUIDE_EPSILON)
            b[j][i] = m[j][i] - a[j][i] * m[j][i]
    return box_mean(a, r), box_mean(b, r)


def bilinear(values, fx, fy):
    """`values` sampled bilinearly at fx, fy, as fractions of the whole
    image, each value at its pixel's center and the nearest edge value past
    the edge."""
    height, width = len(values), len(values[0])
    x = min(max(fx * width - 0.5, 0.0), width - 1)
    y = min(max(fy * height - 0.5, 0.0), height - 1)
    i, j = min(math.floor(x), width - 2), min(math.floor(y), height - 2)
    tx, ty = x - i, y - j
    top = values[j][i] * (1 - tx) + values[j][i + 1] * tx
    bottom = values[j + 1][i] * (1 - tx) + values[j + 1][i + 1] * tx
    return top * (1 - ty) + bottom * ty


# The whole pipeline.

NEUTRAL_GEOMETRY = {
    "orient": {"rotate": 0, "flipH": False, "flipV": False},
    "angle": 0,
    "crop": geometry.FULL,
}


def render(image, operations):
    """The photo rendered with `operations`, as an edit file lists them:
    rows of linear Display P3 colors, unclipped."""
    params = {op["id"]: op["params"] for op in operations if op.get("enabled", True)}
    height, width = len(image), len(image[0])
    frame = {
        "orient": params.get("seura.orient", NEUTRAL_GEOMETRY["orient"]),
        "angle": params.get("seura.straighten", {"angle": 0})["angle"],
        "crop": params.get("seura.crop", geometry.FULL),
    }
    oriented = geometry.oriented_size(frame["orient"], width, height)
    _, _, across, down = geometry.crop_pixels(frame["crop"], *oriented)
    white_balance = params.get("seura.whiteBalance", {"temperature": 0, "tint": 0})
    ev = params.get("seura.exposure", {"ev": 0})["ev"]
    neighborhood = "seura.highlights" in params or "seura.shadows" in params
    a, b = guide(image, white_balance) if neighborhood else (None, None)
    rows = []
    for j in range(down):
        row = []
        for i in range(across):
            # Geometry: where the pixel comes from in the upright photo.
            u = geometry.position(i, j, (width, height), frame)
            color = geometry.sample(image, *u)
            if "seura.redEye" in params:
                color = formulas.red_eye(color, params["seura.redEye"], (width, height), u)
            if "seura.exposure" in params:
                color = formulas.exposure(color, params["seura.exposure"])
            if "seura.whiteBalance" in params:
                color = formulas.white_balance(color, white_balance)
            if neighborhood:
                # The pixel's own log luminance, after white balance and
                # before exposure; the guide where it is in the photo.
                l = log_luminance([v * 2.0**-ev for v in color])
                fx, fy = u[0] / width, u[1] / height
                base = bilinear(a, fx, fy) * l + bilinear(b, fx, fy) + ev
                if "seura.highlights" in params:
                    color = formulas.highlights(color, params["seura.highlights"], base)
                    # base' = base + gain: what seura.shadows uses.
                    base += highlights_gain(params["seura.highlights"], base)
                if "seura.shadows" in params:
                    color = formulas.shadows(color, params["seura.shadows"], base)
            for op, formula in (
                ("seura.contrast", formulas.contrast),
                ("seura.saturation", formulas.saturation),
                ("seura.blackAndWhite", formulas.black_and_white),
                ("seura.sepia", formulas.sepia),
            ):
                if op in params:
                    color = formula(color, params[op])
            if "seura.vignette" in params:
                at = ((i + 0.5) / across, (j + 0.5) / down)
                color = formulas.vignette(color, params["seura.vignette"], at)
            row.append(color)
        rows.append(row)
    return rows


def highlights_gain(params, base):
    """seura.highlights' gain in stops, as in formulas.highlights."""
    return params["amount"] / 100 * 2 * formulas.tone_position(base) ** 3


# The cases: each an edit's operations, in canonical order, as an edit file
# holds them.


def op(id, **params):
    return {"id": f"seura.{id}", "version": 1, "params": params}


CASES = {
    # Tone and color, pixel by pixel.
    "tone": [
        op("exposure", ev=0.6),
        op("whiteBalance", temperature=30, tint=-15),
        op("contrast", amount=40),
        op("saturation", amount=25),
    ],
    # Highlights and shadows, through the guide, with exposure and white
    # balance, which the base takes in.
    "highlights-shadows": [
        op("exposure", ev=-0.3),
        op("whiteBalance", temperature=-20, tint=10),
        op("highlights", amount=-70),
        op("shadows", amount=60),
    ],
    # Turned, flipped, straightened and cropped: the guide and the vignette
    # each follow the pixel to where it is.
    "geometry": [
        op("orient", rotate=90, flipH=True, flipV=False),
        op("straighten", angle=-6.5),
        op("crop", x=0.15, y=0.12, width=0.7, height=0.74, aspect=None),
        op("highlights", amount=-40),
        op("shadows", amount=35),
        op("vignette", amount=-60, size=50),
    ],
    # A turn and no crop: the corners it leaves take the nearest edge pixel.
    "straighten-uncovered": [
        op("straighten", angle=12),
        op("exposure", ev=0.2),
    ],
    # The effects, one after another.
    "effects": [
        op("blackAndWhite", strength=70),
        op("sepia", strength=50),
        op("vignette", amount=45, size=80),
    ],
    # Red-eye on both pupils, measured on the upright photo while the result
    # is turned and cropped to the face.
    "red-eye": [
        op("orient", rotate=270, flipH=False, flipV=False),
        op("crop", x=0.54, y=0.25, width=0.34, height=0.25, aspect="1:1"),
        op(
            "redEye",
            regions=[
                {"x": 0.5859375, "y": 0.6979167, "radius": 0.05},
                {"x": 0.6796875, "y": 0.6979167, "radius": 0.05},
            ],
        ),
    ],
    # Everything at once, with saturation turned off (`enabled`: false),
    # which renders as if it weren't there.
    "everything": [
        op("orient", rotate=180, flipH=False, flipV=True),
        op("straighten", angle=3),
        op("crop", x=0.06, y=0.08, width=0.88, height=0.84, aspect="4:3"),
        op("redEye", regions=[{"x": 0.5859375, "y": 0.6979167, "radius": 0.05}]),
        op("exposure", ev=0.35),
        op("whiteBalance", temperature=15, tint=5),
        op("highlights", amount=-50),
        op("shadows", amount=40),
        op("contrast", amount=-20),
        {**op("saturation", amount=60), "enabled": False},
        op("sepia", strength=30),
        op("vignette", amount=-35, size=65),
    ],
}


def rounded(color):
    """Seven significant digits: far finer than the tolerance."""
    return [float(f"{v:.7g}") for v in color]


def photo_text():
    """The photo's file: its size, then one row of colors to a line."""
    rows = ",\n".join(f"    {json.dumps(row)}" for row in photo())
    head = json.dumps({"width": WIDTH, "height": HEIGHT}, indent=2)
    return head[:-2] + ',\n  "pixels": [\n' + rows + "\n  ]\n}\n"


def case_text(name):
    """A case's file: its operations, one to a line, then the expected
    result's size and rows."""
    operations = CASES[name]
    result = render(photo(), operations)
    head = json.dumps({"photo": "photo.json", "tolerance": TOLERANCE}, indent=2)
    ops = ",\n".join(f"    {json.dumps(item)}" for item in operations)
    rows = ",\n".join(f"    {json.dumps([rounded(color) for color in row])}" for row in result)
    return (
        head[:-2]
        + ',\n  "operations": [\n'
        + ops
        + f'\n  ],\n  "width": {len(result[0])},\n  "height": {len(result)},\n  "output": [\n'
        + rows
        + "\n  ]\n}\n"
    )


def files():
    """Every file's path under tests/reference/, and what makes its text."""
    made = {"photo.json": photo_text}
    made.update({f"{name}.json": (lambda name=name: case_text(name)) for name in CASES})
    return made
