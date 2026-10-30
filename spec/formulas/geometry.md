# Geometry: orient, straighten, and crop

`seura.orient`, `seura.straighten` and `seura.crop` together make one coordinate transform (specification, "Geometry frame and sampling"). Nothing is drawn and then redrawn: each pixel of the result works out where it comes from in the photo, and the photo is sampled there once. This file gives that transform exactly, the filter the photo is sampled with, and, for writers, the largest crop that keeps a straightened photo's corners out of view.

## Frames and positions

- The **upright photo** is the photo as decoded with its orientation metadata applied: w × h pixels. Red-eye regions and the [luminance guide](luminance-guide.md) are measured on it.
- The **oriented photo** is the upright photo with `seura.orient` applied: W × H pixels, which is h × w when `rotate` is 90 or 270, and w × h otherwise. It's the frame `seura.straighten` turns the photo in and `seura.crop` is measured on.
- A **position** is in pixels from the frame's top left corner, x to the right and y down. Pixel (i, j) covers i to i + 1 across and j to j + 1 down, so its center is at (i + 0.5, j + 0.5).
- round(v) is floor(v + 0.5): halves round up.

## From an output pixel to the photo

Without a `seura.crop`, the crop is the whole frame (0, 0, 1, 1); without the others, the angle is 0 and the orientation is upright.

1. **The crop.** In whole pixels of the oriented photo:

   ```
   left = round(x × W)          top = round(y × H)
   Wc = max(1, round(width × W))    Hc = max(1, round(height × H))
   ```

   The result is Wc × Hc pixels. Output pixel (i, j) is at frame position

   ```
   p = (left + i + 0.5, top + j + 0.5)
   ```

2. **The turn.** `seura.straighten` turned the photo θ = `angle` degrees clockwise as seen, about the frame's center c = (W / 2, H / 2). With y down, that's this turn of a point about c, and p is turned back by it:

   ```
   d = p − c
   q = c + (d.x cos θ + d.y sin θ,  −d.x sin θ + d.y cos θ)
   ```

3. **The orientation.** `seura.orient` turned the upright photo clockwise, then flipped it as it was then seen, so q is unflipped, then turned back. First, in the W × H frame:

   ```
   if flipH: q.x = W − q.x
   if flipV: q.y = H − q.y
   ```

   Then, by `rotate`:

   | `rotate` | Position u in the upright photo |
   | --- | --- |
   | 0 | (q.x, q.y) |
   | 90 | (q.y, W − q.x) |
   | 180 | (W − q.x, H − q.y) |
   | 270 | (H − q.y, q.x) |

4. **The sample.** The output pixel is the upright photo sampled at u with Catmull-Rom (below). Its base for highlights and shadows comes from the guide at the same position, u / (w, h) as fractions of the photo.

Without straightening, every u falls on a pixel center, so geometry copies whole pixels exactly.

## Catmull-Rom

The photo is sampled at position u, with its pixels' colors P(i, j) at their centers:

1. **Edges.** A position past the outermost pixel centers moves to the nearest one:

   ```
   x = clamp(u.x, 0.5, w − 0.5)      y = clamp(u.y, 0.5, h − 0.5)
   ```

   So a position past the photo's edge, as in the corners a straightened photo leaves uncovered, takes the nearest edge pixel exactly.
2. **The pixels around it.** With fx = x − 0.5 and fy = y − 0.5, the pixels are columns floor(fx) − 1 to floor(fx) + 2 and rows floor(fy) − 1 to floor(fy) + 2. The ones past the edge repeat the edge pixel: columns are clamped to 0 to w − 1, and rows to 0 to h − 1.
3. **Weights.** With t = fx − floor(fx), the four columns' weights, in order, are:

   ```
   (−t³ + 2t² − t) / 2
   (3t³ − 5t² + 2) / 2
   (−3t³ + 4t² + t) / 2
   (t³ − t²) / 2
   ```

   The rows' are the same with t = fy − floor(fy).
4. **The color** is the sum of the 16 pixels' colors, each times its column's weight and its row's weight. Each channel is computed alike, in the working space.

The weights add up to 1, and at t = 0 they're 0, 1, 0, 0, so a position on a pixel's center returns that pixel. Beside a sharp edge, the result can go a little past the pixels around it, below 0 or above the brighter side. That sharpness is what Catmull-Rom is chosen for, so the result isn't clipped; components below 0 are handled as the [conventions](README.md) say.

## Keeping the corners out of view

This is for writers, and doesn't affect rendering. When the user straightens a photo, the crop shrinks so no uncovered corner shows (Seura Photos, EDT-3). The largest crop that keeps the user's crop's center and shape is the user's crop scaled about its center by s, the largest scale that keeps all four corners on the turned photo.

A frame position p is on the turned photo when q from step 2 above is within 0 to W across and 0 to H down. With R⁻¹ the turn back from step 2, (d.x cos θ + d.y sin θ, −d.x sin θ + d.y cos θ):

- C is the crop's center in pixels, ((x + width / 2) W, (y + height / 2) H), and e = R⁻¹(C − c).
- For each corner k of the crop, with (a, b) = (width × W / 2, height × H / 2), g = R⁻¹(±a, ±b).

If the center isn't on the turned photo, |e.x| > W / 2 or |e.y| > H / 2, no scale fits, and s = 0. Otherwise:

```
s = min(1, over each corner g, and each axis with g's component ≠ 0:
          (W / 2 − sign(g.x) × e.x) / |g.x|,   (H / 2 − sign(g.y) × e.y) / |g.y|)
```

The fitted crop is then centered on C, with width s × width and height s × height. The turned photo is convex, so a crop whose corners are on it is on it entirely. Seura Photos rounds the fitted crop's edges inward to whole pixels before writing it, so rendering's rounding can't move an edge outward.

## Test vectors

In `tests/formulas/geometry/`, computed in double precision by `tools/geometry.py`, with the same tolerance as the other operations' vectors:

- **`positions.json`**: an upright size, `seura.orient`'s, `seura.straighten`'s and `seura.crop`'s params, the output size, and for some of its pixels, the position u each one samples.
- **`sampling.json`**: a 5 × 4 image, and the color Catmull-Rom gives at each of a set of positions, on pixel centers, between them, across a hard edge where it goes past the pixels around it, and on and past the edges.
- **`crop-inside.json`**: a frame size, an angle and a crop, with the scale s and the fitted crop.
