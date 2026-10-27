# twemoji-cbdt

A script that turns the [Twemoji](https://github.com/jdecked/twemoji)
graphics into a color emoji font. Each emoji is a PNG image inside the font
(`CBDT` and `CBLC` tables, the format Noto Color Emoji used before it moved
to `COLRv1`).

The font is called `Twemoji`. It is built from Twemoji 17.0.3, which follows
the Unicode 17 emoji, and handles flags, skin tones and ZWJ sequences with
ligature rules. GTK 4.22.5's emoji picker shows all 1910 emoji it lists with
it.

It is not affiliated with Twitter, X Corp. or the Twemoji project.

## Why bitmaps

Drawing many emoji with a vector color font (`COLR`) fills a glyph cache of
hundreds of megabytes in cairo, which GTK uses to draw in software, and cairo
never frees it. A bitmap font avoids that. In GTK 4.22.5, opening the emoji
picker with the cairo renderer takes an app from about 35 MB to:

| Font | Memory after opening the picker |
|---|---|
| Noto Color Emoji (COLRv1) | 241–608 MB |
| Twemoji 14.0.2 from Fedora (bitmap) | 56 MB, with 1373 emoji shown |
| This font | 63 MB, with all 1910 emoji shown |

The measurements are in
[Wassup's `docs/performance.md`](https://github.com/MawCeron/Wassup/blob/main/docs/performance.md#emoji-picker).
Fedora ships Twemoji 14, which lacks the emoji added to Unicode since; this
font is built from the current artwork.

## Building

You need Python 3 with [fonttools](https://github.com/fonttools/fonttools)
(it provides `ttx`) and [Pillow](https://python-pillow.org/), and `git`:

```sh
sudo dnf install python3-fonttools python3-pillow
./build.sh
```

It downloads the graphics at a pinned version into `build/`, builds
`build/Twemoji.ttf` and checks it. `build_cbdt.py` builds a font from any
directory of PNG files named by code points, like `1f600.png` or
`1f468-200d-1f469-200d-1f467.png`:

```sh
python3 build_cbdt.py PNG_DIR OUT.ttf [FAMILY [VERSION]]
```

## Installing

```sh
mkdir -p ~/.local/share/fonts
cp build/Twemoji.ttf ~/.local/share/fonts/
fc-cache -f
```

Fedora's `twitter-twemoji-fonts` has the same family name, so install only
one of them.

## Limits

- The images are 72 px tall, so the emoji look soft when drawn large.
- It has only been tested with GTK 4.22.5 on Fedora 44.
- If a system also has Symbola, a monochrome symbol font, GTK's emoji picker
  can drop wide emoji such as flags. Hiding Symbola avoids it.

## License

The code is under the [MIT License](LICENSE). The font is an adaptation of
the Twemoji graphics, which are under
[CC BY 4.0](LICENSE-GRAPHICS): credit Twitter and the Twemoji contributors,
and say that the graphics were changed. [NOTICE](NOTICE) has the credit and
the list of changes, and the font carries the license in its name table.
