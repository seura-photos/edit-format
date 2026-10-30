# `seura.sepia`, version 1

**Params:** `strength`, 0 to 100. Neutral: 0.

Blends toward a warm brown monochrome: the color's luminance, Y, in sepia's tone T. T is a warm brown scaled so its own luminance is 1, so the monochrome keeps the photo's brightness. Each channel moves toward Y × T by k = strength / 100.

```
Y = 0.2289746 R + 0.6917385 G + 0.0792869 B
t = (1.25, 0.97, 0.56)
T = t / (0.2289746 × 1.25 + 0.6917385 × 0.97 + 0.0792869 × 0.56)
  ≈ (1.2479966, 0.9684454, 0.5591025)
k = strength / 100
R' = R + (Y × T.r − R) × k
G' = G + (Y × T.g − G) × k
B' = B + (Y × T.b − B) × k
```

Only the luminance of the color before it matters at 100, so a photo in black and white first (`seura.blackAndWhite` comes before it) looks the same at full strength. Nothing is clipped: white comes out with red above 1, a cream once the app clips it for the screen or a file ("Working space" in the [README](README.md)).

**Test vectors:** [`tests/formulas/seura.sepia.json`](../../tests/formulas/seura.sepia.json), at `strength` 25, 60 and 100.
