# `seura.whiteBalance`, version 1

**Params:** `temperature` and `tint`, each −100 to 100. Neutral: both 0.

A shift from the photo as shot, by a gain on each channel. Temperature moves the balance between red and blue: positive warms it toward amber, raising red and lowering blue; negative cools it toward blue. Tint moves green against red and blue: positive moves it toward magenta, lowering green; negative toward green. At 100, each shift is half a stop either way: temperature 100 doubles red relative to blue.

The gains are then scaled together so that a gray keeps its luminance: the photo's overall brightness stays where it was, and only its color moves.

```
t = temperature / 100
n = tint / 100
gR = 2^(t / 2)
gG = 2^(−n / 2)
gB = 2^(−t / 2)
k = 0.2289746 gR + 0.6917385 gG + 0.0792869 gB    (the gains' luminance)
R' = R × gR / k
G' = G × gG / k
B' = B × gB / k
```

The gains are positive, so a component's sign never changes: one below 0 stays below 0, and none is made.

**Test vectors:** [`tests/formulas/seura.whiteBalance.json`](../../tests/formulas/seura.whiteBalance.json), at temperature and tint −100, 100, and combinations between.
