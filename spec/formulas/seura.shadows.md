# `seura.shadows`, version 1

**Params:** `amount`, −100 to 100. Neutral: 0.

Lifts or deepens the dark areas of the photo, such as a backlit face, with little effect on bright ones. Positive amounts lift detail out of shadows; negative amounts deepen them. A neighborhood operation: how dark an area is comes from the pixel's base, from the [luminance guide](luminance-guide.md), as `seura.highlights` left it.

As for highlights, the base is turned into x, from black (0) to white (1). The gain, in stops, is the amount's share of 2 stops, weighed by (1 − x)³. So it's full at black, an eighth at x = 0.5, and nothing at white.

```
x = clamp(2^base, 0, 1)^(1 / 2.2)
gain = amount / 100 × 2 × (1 − x)³
R' = R × 2^gain
G' = G × 2^gain
B' = B × 2^gain
```

The color keeps its hue and saturation. Noise in deep shadows is lifted along with them.

**Test vectors:** [`tests/formulas/seura.shadows.json`](../../tests/formulas/seura.shadows.json). As for highlights, each case gives the pixel's `base` beside its input color. The cases use `amount` −100, −50, 30 and 100.
