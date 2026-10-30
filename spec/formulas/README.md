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

**Order.** Operations run in the specification's canonical order, each on the result of the one before. An operation whose settings are all neutral changes nothing. Writers remove such an operation from the file, and readers may skip it.

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

A neighborhood operation's output also depends on the pixel's surroundings, through its base from the [luminance guide](luminance-guide.md). Its cases each give that `base`, in stops of log2 luminance, beside the input color, so the formula can be checked on its own. Reference images for checking a whole guide are planned for 1.0.

`python tools/formulas.py` regenerates the vectors after a formula changes, and `python tools/check.py --self-test` fails if they're out of date.

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
