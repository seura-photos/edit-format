# Formulas appendix

The exact math for each core operation, as the specification promises ("Core operations"), written from the reference implementation in Seura Photos. One file per operation, named by its ID. An operation without a file here isn't defined exactly yet; its meaning is the specification's table.

Each file gives the formula in words and pseudocode, and points to its test vectors. A reader that renders an operation SHOULD match its vectors within the tolerance below.

## Conventions

**Working space.** Every operation takes and returns colors as linear light with Display P3 primaries and the D65 white point: three numbers, red, green and blue, where 0 is black and 1 is the photo's reference white. Values aren't clipped between operations: exposure and contrast can take a color above 1, and the next operation sees it as it is. Components can be below 0 for colors outside Display P3, from a wider-gamut original. Every operation accepts them, and a formula says if it can produce them itself. How the result is encoded and clipped for a screen or a file is up to the app, not the format.

**Luminance.** Where a formula needs a color's luminance, it's

```
Y = 0.2289746 R + 0.6917385 G + 0.0792869 B
```

the middle row of the matrix from linear Display P3 to CIE XYZ.

**Order.** Operations run in the specification's canonical order, each on the result of the one before. An operation whose settings are all neutral changes nothing. Writers remove such an operation from the file, and readers may skip it. An operation with `enabled` false is skipped, as if it weren't in the file. [The whole pipeline](#the-whole-pipeline) gives the order for one pixel.

**Precision.** Formulas are written with real numbers; at least 32-bit floating point is expected.

## Test vectors

`tests/formulas/<operation id>.json` holds each operation's vectors: input colors in the working space, the operation's `params`, and the expected output, computed in double precision by `tools/formulas.py`. Inputs are values that half-precision floats hold exactly, such as 0.125 or 0.75, so an implementation that stores pixels as 16-bit floats can feed them in unchanged.

An output component matches when it's within the file's tolerance:

```
|found − expected| ≤ absolute + relative × |expected|
```

with `absolute` 0.0001 and `relative` 0.001 throughout. That's far finer than an 8-bit output can show, and coarse enough for a GPU's floating point.

The geometry stage's vectors are positions and a small image, not colors alone, and are in `tests/formulas/geometry/`, as [geometry.md](geometry.md) describes.

An operation measured on the cropped frame, such as the vignette, depends on where the pixel is: its cases each give that `position`, as fractions of the frame, beside the input color. Red-eye's depend on where the pixel is in the upright photo: its cases give the photo's `size` and the `position`, in its pixels.

A neighborhood operation's output also depends on the pixel's surroundings, through its base from the [luminance guide](luminance-guide.md). Its cases each give that `base`, in stops of log2 luminance, beside the input color, so the formula can be checked on its own. The [reference images](#reference-images) check the whole guide.

`python tools/formulas.py` regenerates the vectors after a formula changes, and `python tools/check.py --self-test` fails if they're out of date.

## The whole pipeline

Each pixel of the result is worked out on its own, in one pass:

1. **Where it comes from.** Its center is mapped through `seura.crop`, `seura.straighten` and `seura.orient` to a position u in the upright photo, and the photo is sampled there with Catmull-Rom ([geometry.md](geometry.md)).
2. **Red-eye**, by u, on the upright photo's pixels ([seura.redEye.md](seura.redEye.md)).
3. **Exposure, then white balance.**
4. **Highlights, then shadows.** The pixel's base is the [luminance guide](luminance-guide.md) at u, with the pixel's own log luminance as it is now, without exposure. The guide itself is built from the whole upright photo as decoded, so red-eye and geometry don't change it; only white balance does.
5. **Contrast, then saturation, then black and white, then sepia.**
6. **The vignette**, by the pixel's place in the result, which is the cropped frame ([seura.vignette.md](seura.vignette.md)).

Non-core operations run after the core ones in their stage. The result is linear Display P3, unclipped; encoding it for a screen or a file is up to the app.

## Reference images

`tests/reference/` checks a whole render, not one formula at a time: a small photo, `photo.json`, and cases, each an edit's `operations` exactly as an edit file holds them, with the expected result.

- **The photo** is 64 × 48 pixels, upright: a sky with a sun brighter than white, a dark tree against it, the ground, a face with two red pupils, and a row of colors along the bottom, one outside Display P3. Its `pixels` are rows, top to bottom, of linear Display P3 colors that half-precision floats hold exactly. It's smaller than the guide's 1024 pixels, so the guide is built on the photo itself, and the downscaling filter, which the format leaves to the app, plays no part.
- **Each case** gives the result's `width` and `height`, which test the crop's rounding, and its `output`, rows of linear Display P3 colors, unclipped, as [the whole pipeline](#the-whole-pipeline) leaves them. A reader matches when every component is within the `tolerance`, as for the test vectors, or, if it compares encoded 8-bit results, within one level.

| Case | What it checks |
| --- | --- |
| `tone` | Exposure, white balance, contrast and saturation, pixel by pixel |
| `highlights-shadows` | The guide, with the exposure and white balance its base takes in |
| `geometry` | A turn, a flip, straightening and a crop, with the guide and the vignette following each pixel |
| `straighten-uncovered` | Straightening without a crop: the uncovered corners take the nearest edge pixel |
| `effects` | Black and white, sepia, and a lightening vignette |
| `red-eye` | Both pupils corrected on a photo turned and cropped to the face, the regions on the upright photo |
| `everything` | Every stage at once, with saturation turned off by `enabled` |

`tools/reference.py` renders them in double precision with the same formulas as the test vectors, and `python tools/formulas.py` writes them with the vectors. Seura Photos' tests render every case on the GPU and compare.

## Operations

| Operation | File |
| --- | --- |
| `seura.orient`, `seura.straighten`, `seura.crop` | [geometry.md](geometry.md), with Catmull-Rom sampling |
| `seura.redEye` | [seura.redEye.md](seura.redEye.md) |
| `seura.exposure` | [seura.exposure.md](seura.exposure.md) |
| `seura.whiteBalance` | [seura.whiteBalance.md](seura.whiteBalance.md) |
| `seura.highlights` | [seura.highlights.md](seura.highlights.md), with the [luminance guide](luminance-guide.md) |
| `seura.shadows` | [seura.shadows.md](seura.shadows.md), with the [luminance guide](luminance-guide.md) |
| `seura.contrast` | [seura.contrast.md](seura.contrast.md) |
| `seura.saturation` | [seura.saturation.md](seura.saturation.md) |
| `seura.blackAndWhite` | [seura.blackAndWhite.md](seura.blackAndWhite.md) |
| `seura.sepia` | [seura.sepia.md](seura.sepia.md) |
| `seura.vignette` | [seura.vignette.md](seura.vignette.md) |
