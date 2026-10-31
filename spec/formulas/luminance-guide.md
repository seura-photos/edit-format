# The luminance guide

`seura.highlights` and `seura.shadows` are neighborhood operations (specification, "Neighborhood operations"): how much each changes a pixel depends on how bright the area around it is. That brightness is the pixel's **base**, read from a **luminance guide**, an edge-preserving smoothing of the photo's log luminance. It's a guided filter guided by itself (He, Sun and Tang, "Guided Image Filtering", 2010). It smooths over texture but not across strong edges, so a dark tree against a bright sky keeps a sharp boundary between its base and the sky's, and no halo appears along the edge.

## Building the guide

The guide is built once for the whole upright photo (the photo with its orientation metadata applied, as [geometry.md](geometry.md) defines it), before any geometry operation (`seura.orient`, `seura.straighten`, `seura.crop`), and each output pixel looks it up at its position in that photo, the same position geometry samples the photo at. So rotating, flipping, straightening and cropping never change how highlights and shadows look, and the corners a turned photo leaves uncovered never enter the guide. (With straightening, the guide's square averages are square in the photo rather than on screen, a difference too small to see.)

1. **The guide image.** The photo is scaled to fit 1024 pixels on its long side, or kept as it is if it's smaller. Any downscaling filter that averages all the source pixels each guide pixel covers will do, such as an area average, bilinear with a box prefilter, or Lanczos; one that picks single pixels, such as nearest-neighbor, will not, since it lets fine detail alias into the guide. After the guide's 41-pixel averages, the difference between good filters is far below what can be seen. Seura scales the decoded photo with a Lanczos filter before converting it to the working space. Call its size W × H, and its long side L = max(W, H).
2. **Log luminance.** For each pixel of the guide image, white balance (`seura.whiteBalance`) is applied with the file's settings, but not exposure. Then:

   ```
   Y = 0.2289746 R + 0.6917385 G + 0.0792869 B
   l = log2(max(Y, 2^−12))
   ```

   The floor, about a sixteenth of the darkest 8-bit level, keeps black from counting as infinitely dark.
3. **Means.** With radius r = max(1, round(0.02 × L)), which is 20 pixels at 1024, mean(v) is the average of v over the (2r + 1) × (2r + 1) square around each pixel. Pixels past the image's edge repeat the nearest edge pixel. It's computed as a mean across, then a mean down.
4. **Coefficients.** For each guide pixel, with ε = 0.1 (stops squared):

   ```
   m = mean(l)
   v = max(mean(l²) − m², 0)
   a = v / (v + ε)
   b = m − a × m
   ```

   Where the area varies less than ε, a is near 0 and the base is the area's mean. Across an edge, the variance is large, a is near 1, and the base follows the pixel itself.
5. **The guide** is A = mean(a) and B = mean(b), with the same radius.

## A pixel's base

For a pixel of the photo at any resolution, A and B are sampled bilinearly at the pixel's position within the whole photo. Each guide pixel's value sits at its center, and positions past the edge take the nearest edge value. Then, with l the pixel's own log luminance after white balance and before exposure, computed as in step 2, and ev the file's exposure:

```
base = A × l + B + ev
```

Using the pixel's own l, not the guide's, keeps edges as sharp as the photo however small the guide is. Exposure shifts every log luminance by ev, so it's added here rather than built into the guide.

`seura.highlights` then changes the pixel and the base by its gain (see [seura.highlights.md](seura.highlights.md)), and `seura.shadows` uses the base as `seura.highlights` left it.

Reference images with expected results, for checking a whole guide, are planned for the specification's 1.0 release.
