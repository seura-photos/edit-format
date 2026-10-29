# `seura.contrast`, version 1

**Params:** `amount`, −100 to 100. Neutral: 0.

An S-shaped curve around middle gray, applied to the color's luminance. Positive amounts darken tones below middle gray and brighten those above it; negative amounts move both toward middle gray. Black, middle gray (luminance 0.18) and white (luminance 1) stay where they are, and light above white is left as it is.

The curve works on luminance raised to 1/2.2, which spaces tones roughly as the eye sees them, so the shadows and the highlights are shaped evenly. It has two halves that meet at middle gray, where its slope is g = 2^(amount / 100): at 100 the tones around middle gray are spread twice as far apart, at −100 half as far. The color keeps its hue and saturation: each channel is scaled by the luminance's change.

```
Y = 0.2289746 R + 0.6917385 G + 0.0792869 B
if Y ≤ 0: the color is unchanged
x = Y^(1 / 2.2)
if x ≥ 1: the color is unchanged
g = 2^(amount / 100)
p = 0.18^(1 / 2.2)                              (middle gray)
x' = p × (x / p)^g                              if x < p
x' = 1 − (1 − p) × ((1 − x) / (1 − p))^g        otherwise
s = x'^2.2 / Y
R' = R × s
G' = G × s
B' = B × s
```

The scale s is positive, so a component's sign never changes: one below 0 stays below 0, and none is made.

**Test vectors:** [`tests/formulas/seura.contrast.json`](../../tests/formulas/seura.contrast.json), at `amount` −100, −40, 25, 60 and 100.
