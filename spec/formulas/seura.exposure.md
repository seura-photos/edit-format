# `seura.exposure`, version 1

**Params:** `ev`, −4 to 4. Neutral: 0.

Brightness in photographic stops. Each stop doubles or halves the light, so every channel is multiplied by 2 to the power `ev`. Colors keep their hue and saturation; values above 1 are kept for the operations that follow.

```
s = 2^ev
R' = R × s
G' = G × s
B' = B × s
```

**Test vectors:** [`tests/formulas/seura.exposure.json`](../../tests/formulas/seura.exposure.json), at `ev` −4, −1.5, 0.3, 1 and 4.
