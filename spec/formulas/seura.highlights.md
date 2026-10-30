# `seura.highlights`, version 1

**Params:** `amount`, −100 to 100. Neutral: 0.

Darkens or brightens the bright areas of the photo, such as a sky, with little effect on dark ones. Negative amounts recover detail in bright areas; positive amounts brighten them. A neighborhood operation: how bright an area is comes from the pixel's base, from the [luminance guide](luminance-guide.md).

The base is turned into x, a position from black (0) to white (1), spaced roughly as the eye sees tones. The gain, in stops, is the amount's share of 2 stops, weighed by x³. So it's full at white, an eighth at x = 0.5, and nothing at black.

```
x = clamp(2^base, 0, 1)^(1 / 2.2)
gain = amount / 100 × 2 × x³
R' = R × 2^gain
G' = G × 2^gain
B' = B × 2^gain
base' = base + gain
```

The color keeps its hue and saturation. `base'` is the base `seura.shadows` uses next.

A pixel that's pure white in the original has nothing left to recover: negative amounts darken it to a gray.

**Test vectors:** [`tests/formulas/seura.highlights.json`](../../tests/formulas/seura.highlights.json). The output depends on the pixel's neighborhood, so each case gives the pixel's `base` beside its input color. The cases use `amount` −100, −50, 30 and 100, at bases from deep shadow to above white.
