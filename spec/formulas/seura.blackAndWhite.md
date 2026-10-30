# `seura.blackAndWhite`, version 1

**Params:** `strength`, 0 to 100. Neutral: 0.

Blends toward a luminance-only image. Each channel moves toward the color's luminance by k = strength / 100: at 100 every color becomes the gray of its own luminance, and between, the color fades toward it. Luminance is unchanged, so the photo's brightness stays where it was.

```
Y = 0.2289746 R + 0.6917385 G + 0.0792869 B
k = strength / 100
R' = R + (Y − R) × k
G' = G + (Y − G) × k
B' = B + (Y − B) × k
```

At 100 it's the same as `seura.saturation` at −100. Nothing is clipped: a component below 0, from a color outside Display P3, moves toward Y like any other.

**Test vectors:** [`tests/formulas/seura.blackAndWhite.json`](../../tests/formulas/seura.blackAndWhite.json), at `strength` 25, 60 and 100.
