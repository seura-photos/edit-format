# `seura.vignette`, version 1

**Params:** `amount`, −100 to 100; `size`, 0 to 100. Neutral: `amount` 0, whatever the size.

Darkens the edges of the photo (negative amounts) or lightens them (positive amounts), more toward the corners. Measured on the cropped frame: the result of the geometry stage, w × h pixels. The shape is an ellipse fitted to that frame, so the vignette follows the photo's shape, and its size is a fraction of the frame, so it looks the same at any resolution.

Each pixel's position is its center, as fractions of the frame from its top left corner: u = (i + 0.5) / w, v = (j + 0.5) / h for the pixel in column i and row j. Its distance from the center, r, is 0 there, 1 at the middle of each edge, and √2 at the corners. The vignette starts at r = 1 − size / 100 and grows smoothly to its full amount at the corners: size 0 touches only the corners, past the ellipse through the edges' middles; size 100 starts at the center.

```
d = (2u − 1, 2v − 1)
r = √(d.x² + d.y²)
start = 1 − size / 100
t = clamp((r − start) / (√2 − start), 0, 1)
m = amount / 100 × t² (3 − 2t)
if m < 0:  R' = R × (1 + m)            (and G, B the same)
else:      R' = R + (1 − R) × m        (and G, B the same)
```

Darkening scales the color toward black, keeping its hue; at −100 the very corners are black. Lightening blends toward white, so bright colors don't change hue as they would if scaled; at 100 the very corners are white. A value above 1 is blended down toward 1 by a positive amount.

**Test vectors:** [`tests/formulas/seura.vignette.json`](../../tests/formulas/seura.vignette.json). The output depends on where the pixel is, so each case gives its `position`, u and v, beside its input color. The cases use (`amount`, `size`) of (−100, 0), (−25, 60), (40, 30) and (100, 100), at the center, toward an edge, toward a corner, and near one.
