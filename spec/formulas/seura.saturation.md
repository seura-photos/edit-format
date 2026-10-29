# `seura.saturation`, version 1

**Params:** `amount`, −100 to 100. Neutral: 0.

How colorful the photo is. Each channel moves away from the color's luminance, or toward it, by the same factor s = 1 + amount / 100: at −100 every color becomes the gray of its own luminance, and at 100 its difference from that gray is doubled. Luminance is unchanged, so the photo's brightness stays where it was.

```
Y = 0.2289746 R + 0.6917385 G + 0.0792869 B
s = 1 + amount / 100
R' = Y + (R − Y) × s
G' = Y + (G − Y) × s
B' = Y + (B − Y) × s
```

Nothing is clipped. A component below 0, from a color outside Display P3, is used as it is. Raising saturation can also make components below 0 itself: a vivid color made more vivid can move outside Display P3, and its weakest channel goes negative. At 100, the input (0.9375, 0.875, 0.0625) comes out with blue at about −0.70. Values above 1 are kept the same way. How such colors are shown or exported is up to the app ("Working space" in the [README](README.md)).

**Test vectors:** [`tests/formulas/seura.saturation.json`](../../tests/formulas/seura.saturation.json), at `amount` −100, −50, 30, 60 and 100.
