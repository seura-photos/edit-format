# `seura.redEye`, version 1

**Params:** `regions`, a list of circles `{x, y, radius}`. Neutral: no regions.

Each circle darkens and desaturates red pupils inside it. Only red pixels change, so a circle drawn generously around a pupil leaves the iris, the white of the eye, lashes and skin as they are, and keeps the catchlight, which isn't red.

**Where.** The regions are on the upright photo: the photo with its orientation metadata applied, before any geometry operation, W × H pixels (edit format, "Coordinates"). A circle's center is (x × W, y × H), and its radius in pixels is ρ = radius × min(W, H). A pixel's position p is where the geometry stage samples the photo for it ([geometry.md](geometry.md)), in the same pixels, so the circles stay on the eyes however the photo is turned, straightened or cropped.

**How much, by place.** Each circle's weight is 1 inside four fifths of its radius, falls smoothly to 0 at its edge, and is 0 beyond, so there's no ring. Where circles overlap, the largest weight counts, so a pixel is never corrected twice.

**How much, by color.** How red the pixel is: its red's lead over the larger of its green and blue, as a share of its red. Red pupils, in linear light, are above 0.85; skin, even reddish skin, stays below about 0.76, and a brown iris lower still. The correction starts at 0.7 and is full at 0.9.

**The correction.** The red comes down toward the larger of green and blue. A red pupil becomes the dark, nearly gray color its green and blue already have. Green and blue don't change.

```
smoothstep(a, b, v) = t² (3 − 2t), with t = clamp((v − a) / (b − a), 0, 1)

for each region:
  c = (x × W, y × H)
  ρ = radius × min(W, H)
  w_region = 1 − smoothstep(0.8, 1, |p − c| / ρ)
w = the largest w_region, or 0 with no region

m = max(G, B)
if w = 0, or R ≤ 0, or R ≤ m:  unchanged
s = (R − m) / R
k = smoothstep(0.7, 0.9, s)
R' = R + (m − R) × w × k
G' = G
B' = B
```

Nothing is clipped. Red-eye runs before tone and color (the specification's order), so it sees the photo's own colors. The [luminance guide](luminance-guide.md) is built from the photo as decoded, without red-eye; a pixel's own luminance, which highlights and shadows also use, is taken after it.

**Test vectors:** [`tests/formulas/seura.redEye.json`](../../tests/formulas/seura.redEye.json). Each case gives the upright photo's `size` and the pixel's `position` in it, in pixels, beside its input color. Here that's 400 × 300, with one circle centered at (100, 150) with a 15-pixel radius, and then two overlapping circles. The positions fall at a center, inside the soft edge, halfway through it, and outside. The inputs add red pupils of several shades, a reddish skin and a brown iris to the usual colors.
