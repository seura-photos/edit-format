"""Test vectors for the geometry stage (spec/formulas/geometry.md), written
to tests/formulas/geometry/ by tools/formulas.py.

Each formula is written here in double precision, exactly as geometry.md
gives it:

- positions: where an output pixel's center comes from in the upright photo,
  through the crop, the turn, and seura.orient;
- sampling: Catmull-Rom on a small image, at chosen positions;
- crop-inside: how far a crop shrinks about its center to fit inside the
  turned photo.
"""

import math


def round_half_up(value):
    """round() in geometry.md: halves round up."""
    return math.floor(value + 0.5)


def crop_pixels(crop, width, height):
    """The crop's left, top, width and height in whole pixels of the
    oriented photo's W × H frame; never smaller than one pixel."""
    left = round_half_up(crop["x"] * width)
    top = round_half_up(crop["y"] * height)
    across = max(1, round_half_up(crop["width"] * width))
    down = max(1, round_half_up(crop["height"] * height))
    return left, top, across, down


def oriented_size(orient, width, height):
    """The oriented photo's size, for an upright photo of width × height."""
    return (height, width) if orient["rotate"] % 180 == 90 else (width, height)


def unturn(point, angle, width, height):
    """Where a point of the frame was before seura.straighten turned the
    photo `angle` degrees clockwise about its center: the point turned back,
    counter-clockwise, about the frame's center. y grows downward."""
    theta = math.radians(angle)
    cx, cy = width / 2, height / 2
    dx, dy = point[0] - cx, point[1] - cy
    return (
        cx + dx * math.cos(theta) + dy * math.sin(theta),
        cy - dx * math.sin(theta) + dy * math.cos(theta),
    )


def unorient(point, orient, width, height):
    """Where a point of the oriented photo (W × H) is in the upright photo:
    seura.orient's flips undone, then its turn."""
    x, y = point
    if orient["flipH"]:
        x = width - x
    if orient["flipV"]:
        y = height - y
    rotate = orient["rotate"]
    if rotate == 90:
        return (y, width - x)
    if rotate == 180:
        return (width - x, height - y)
    if rotate == 270:
        return (height - y, x)
    return (x, y)


def position(i, j, upright, geometry):
    """The center of output pixel i, j, as a position in the upright photo."""
    width, height = oriented_size(geometry["orient"], *upright)
    left, top, _, _ = crop_pixels(geometry["crop"], width, height)
    point = (left + i + 0.5, top + j + 0.5)
    point = unturn(point, geometry["angle"], width, height)
    return unorient(point, geometry["orient"], width, height)


def catmull_rom_weights(t):
    """The weights of the four pixels around a position, t of the way from
    the second to the third."""
    return [
        (-(t**3) + 2 * t**2 - t) / 2,
        (3 * t**3 - 5 * t**2 + 2) / 2,
        (-3 * t**3 + 4 * t**2 + t) / 2,
        (t**3 - t**2) / 2,
    ]


def sample(image, x, y):
    """Catmull-Rom at position x, y of `image` (rows of colors), pixel
    centers at k + 0.5. A position past the outermost pixel centers moves to
    the nearest one, so past the edge is the nearest edge pixel exactly;
    the pixels the filter reaches past the edge repeat the edge pixel."""
    height, width = len(image), len(image[0])
    x = min(max(x, 0.5), width - 0.5)
    y = min(max(y, 0.5), height - 0.5)
    fx, fy = x - 0.5, y - 0.5
    ix, iy = math.floor(fx), math.floor(fy)
    wx, wy = catmull_rom_weights(fx - ix), catmull_rom_weights(fy - iy)
    color = [0.0, 0.0, 0.0]
    for n in range(4):
        row = image[min(max(iy - 1 + n, 0), height - 1)]
        for m in range(4):
            pixel = row[min(max(ix - 1 + m, 0), width - 1)]
            weight = wx[m] * wy[n]
            color = [c + weight * v for c, v in zip(color, pixel)]
    return color


def shrink_to_fit(crop, angle, width, height):
    """The largest scale, at most 1, of `crop` about its own center that
    keeps it inside the photo turned `angle` degrees: each corner, turned
    back, must lie in the W × H rectangle. 0 if the crop's center isn't
    covered."""
    theta = math.radians(angle)
    cos, sin = math.cos(theta), math.sin(theta)

    def back(dx, dy):
        return (dx * cos + dy * sin, -dx * sin + dy * cos)

    center = ((crop["x"] + crop["width"] / 2) * width, (crop["y"] + crop["height"] / 2) * height)
    half = (crop["width"] * width / 2, crop["height"] * height / 2)
    e = back(center[0] - width / 2, center[1] - height / 2)
    if abs(e[0]) > width / 2 or abs(e[1]) > height / 2:
        return 0.0
    scale = 1.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            g = back(sx * half[0], sy * half[1])
            for gk, ek, limit in ((g[0], e[0], width / 2), (g[1], e[1], height / 2)):
                if gk != 0:
                    scale = min(scale, (limit - math.copysign(1, gk) * ek) / abs(gk))
    return max(scale, 0.0)


def shrunk(crop, scale, width, height):
    """`crop` scaled by `scale` about its center, as fractions."""
    cx, cy = crop["x"] + crop["width"] / 2, crop["y"] + crop["height"] / 2
    w, h = crop["width"] * scale, crop["height"] * scale
    return {"x": cx - w / 2, "y": cy - h / 2, "width": w, "height": h}


def rounded(values):
    return [float(f"{v:.9g}") for v in values]


ORIENTS = [
    {"rotate": rotate, "flipH": flip_h, "flipV": flip_v}
    for rotate in (0, 90, 180, 270)
    for flip_h, flip_v in ((False, False), (True, False), (False, True))
]

FULL = {"x": 0, "y": 0, "width": 1, "height": 1}

# Upright photos that aren't square, one with odd sides; turns, crops whose
# edges round, and both together.
POSITION_CASES = (
    [{"upright": [6, 4], "orient": orient, "angle": 0, "crop": FULL} for orient in ORIENTS]
    + [
        {"upright": [7, 5], "orient": {"rotate": 0, "flipH": False, "flipV": False}, "angle": angle, "crop": FULL}
        for angle in (2.5, -30, 45)
    ]
    + [
        {"upright": [7, 5], "orient": {"rotate": 0, "flipH": False, "flipV": False}, "angle": 0, "crop": crop}
        for crop in (
            {"x": 0.25, "y": 0.1, "width": 0.5, "height": 0.7},
            {"x": 0.07, "y": 0.3, "width": 0.93, "height": 0.5},
        )
    ]
    + [
        {
            "upright": [7, 5],
            "orient": {"rotate": 90, "flipH": True, "flipV": False},
            "angle": -12.5,
            "crop": {"x": 0.2, "y": 0.15, "width": 0.6, "height": 0.55},
        }
    ]
)


def position_case(case):
    upright = tuple(case["upright"])
    width, height = oriented_size(case["orient"], *upright)
    _, _, across, down = crop_pixels(case["crop"], width, height)
    pixels = sorted({(0, 0), (across - 1, 0), (0, down - 1), (across - 1, down - 1), (across // 2, down // 2)})
    return {
        **case,
        "outputSize": [across, down],
        "pixels": [list(p) for p in pixels],
        "positions": [rounded(position(i, j, upright, case)) for i, j in pixels],
    }


# A 5 × 4 image of colors half-precision floats hold exactly: a ramp in red,
# another in green, and a hard step in blue, where Catmull-Rom overshoots.
SAMPLING_IMAGE = [
    [[x / 8, y / 4, 1.0 if x >= 2 else 0.0] for x in range(5)]
    for y in range(4)
]

# Pixel centers (copied exactly), between pixels, across the step, near and
# past the edges, and far outside, which takes the corner pixel.
SAMPLING_POSITIONS = [
    [0.5, 0.5],
    [2.5, 1.5],
    [4.5, 3.5],
    [1.0, 1.5],
    [2.0, 2.0],
    [1.25, 0.75],
    [2.75, 2.25],
    [3.1, 1.9],
    [0.2, 3.8],
    [0.0, 0.0],
    [5.0, 4.0],
    [-3.0, -2.0],
    [9.0, 7.5],
]


def sampling():
    return {
        "image": SAMPLING_IMAGE,
        "cases": [{"position": p, "output": rounded(sample(SAMPLING_IMAGE, *p))} for p in SAMPLING_POSITIONS],
    }


CROP_INSIDE_CASES = [
    {"frame": [6000, 4000], "angle": angle, "crop": crop}
    for angle in (0, 2.5, -7.3, 30, 45)
    for crop in (
        FULL,
        {"x": 0.1, "y": 0.2, "width": 0.5, "height": 0.4},
        {"x": 0.45, "y": 0.0, "width": 0.55, "height": 1},
    )
] + [{"frame": [3000, 4000], "angle": 10, "crop": FULL}]


def crop_inside_case(case):
    width, height = case["frame"]
    scale = shrink_to_fit(case["crop"], case["angle"], width, height)
    crop = shrunk(case["crop"], scale, width, height)
    return {
        **case,
        "scale": float(f"{scale:.9g}"),
        "fitted": dict(zip(crop, rounded(crop.values()))),
    }


TOLERANCE = {"absolute": 0.0001, "relative": 0.001}

FILES = {
    "positions": lambda: {"cases": [position_case(case) for case in POSITION_CASES]},
    "sampling": sampling,
    "crop-inside": lambda: {"cases": [crop_inside_case(case) for case in CROP_INSIDE_CASES]},
}


def build(name):
    built = FILES[name]()
    return {"vectors": f"geometry/{name}", "tolerance": TOLERANCE, **built}
