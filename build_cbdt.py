"""Builds a CBDT (color bitmap) emoji font from a directory of PNG files named by
code points, like Twemoji's assets/72x72: 1f600.png, 1f468-200d-1f469.png.

usage: build_cbdt.py PNG_DIR OUT.ttf [FAMILY [VERSION]]
"""
import io
import os
import subprocess
import sys
import tempfile

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.fontBuilder import FontBuilder
from PIL import Image

png_dir, out_path = sys.argv[1], sys.argv[2]
family = sys.argv[3] if len(sys.argv) > 3 else "Twemoji CBDT"
version = sys.argv[4] if len(sys.argv) > 4 else "1.0"

UPM = 2048
ADVANCE = 2550  # 1.245 em, like Noto Color Emoji: 76 px at 61 ppem
PPEM = 61
BMP_W, BMP_H = 76, 72  # advance and height in pixels at PPEM
BEARING_Y = 57
ZERO_WIDTH = {0x200D, 0xFE0F, 0x20E3} | set(range(0xE0020, 0xE0080))
VS16 = 0xFE0F


def glyph_name(cps):
    return "u" + "_".join("%04X" % c for c in cps)


# 1. The images, as sequences of code points.
files = {}
for n in sorted(os.listdir(png_dir)):
    if n.endswith(".png"):
        cps = tuple(int(p, 16) for p in n[:-4].split("-"))
        files[cps] = os.path.join(png_dir, n)

# 2. Ligature rules: each sequence, with and without U+FE0F after its first
#    code point, since the picker writes emoji fully qualified.
rules = {}
for cps, _ in files.items():
    if len(cps) < 2:
        continue
    variants = {cps, tuple(c for c in cps if c != VS16)}
    if cps[1] != VS16:
        variants.add((cps[0], VS16) + cps[1:])
    for v in variants:
        if len(v) > 1:
            rules.setdefault(v, cps)

# 3. Glyphs: .notdef, blanks (components with no image), then every image
#    glyph in a row, so one index subtable covers the bitmaps.
components = {c for seq in rules for c in seq}
blank = sorted(c for c in components if (c,) not in files)
image_glyphs = [glyph_name(cps) for cps in sorted(files)]
order = [".notdef"] + [glyph_name((c,)) for c in blank] + image_glyphs
cmap = {c: glyph_name((c,)) for c in blank}
cmap.update({cps[0]: glyph_name(cps) for cps in files if len(cps) == 1})

metrics = {".notdef": (0, 0)}
for c in blank:
    metrics[glyph_name((c,))] = (0 if c in ZERO_WIDTH else ADVANCE, 0)
for g in image_glyphs:
    metrics[g] = (ADVANCE, 0)

# 4. The font without images.
fb = FontBuilder(UPM, isTTF=True)
fb.setupGlyphOrder(order)
fb.setupCharacterMap(cmap)
fb.setupHorizontalMetrics(metrics)
fb.setupHorizontalHeader(ascent=1900, descent=-500)
fb.setupNameTable({
    "familyName": family,
    "styleName": "Regular",
    "fullName": family,
    "psName": family.replace(" ", "") + "-Regular",
    "uniqueFontIdentifier": family.replace(" ", "") + "-" + version,
    "version": "Version " + version,
    "copyright": "Graphics: Copyright (c) 2014-2021 Twitter; (c) 2022-present Jason Sofonia & Justine De Caires, CC BY 4.0",
    "licenseDescription": "The graphics are licensed under CC BY 4.0; credit Twitter and the Twemoji contributors and note that they were changed.",
    "licenseInfoURL": "https://creativecommons.org/licenses/by/4.0/",
})
fb.setupOS2(sTypoAscender=1900, sTypoDescender=-500, usWinAscent=1900, usWinDescent=500, sxHeight=0, sCapHeight=0)
fb.setupPost(keepGlyphNames=True)
fea = "languagesystem DFLT dflt;\nfeature ccmp {\n"
for seq, target in sorted(rules.items(), key=lambda kv: (-len(kv[0]), kv[0])):
    fea += "  sub %s by %s;\n" % (" ".join(glyph_name((c,)) for c in seq), glyph_name(target))
fea += "} ccmp;\n"
addOpenTypeFeaturesFromString(fb.font, fea)

# 5. The images: 72x72 PNG centered in a 76x72 canvas, as 8-bit palette PNGs.
def png_bytes(path):
    im = Image.open(path).convert("RGBA")
    canvas = Image.new("RGBA", (BMP_W, BMP_H), (0, 0, 0, 0))
    canvas.paste(im, ((BMP_W - im.width) // 2, 0))
    q = canvas.quantize(256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    buf = io.BytesIO()
    q.save(buf, "PNG", optimize=True)
    return buf.getvalue()

lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<ttFont>', '  <CBDT>', '    <header version="3.0"/>', '    <strikedata index="0">']
for cps in sorted(files):
    data = png_bytes(files[cps]).hex()
    hexlines = "\n".join("          " + " ".join(data[i:i + 8] for i in range(j, min(j + 32, len(data)), 8)) for j in range(0, len(data), 32))
    lines += [
        '      <cbdt_bitmap_format_17 name="%s">' % glyph_name(cps),
        '        <SmallGlyphMetrics>',
        '          <height value="%d"/><width value="%d"/><BearingX value="0"/><BearingY value="%d"/><Advance value="%d"/>' % (BMP_H, BMP_W, BEARING_Y, BMP_W),
        '        </SmallGlyphMetrics>',
        '        <rawimagedata>', hexlines, '        </rawimagedata>',
        '      </cbdt_bitmap_format_17>',
    ]
lines += ['    </strikedata>', '  </CBDT>', '</ttFont>']

first_id = order.index(image_glyphs[0])
last_id = len(order) - 1
line_metrics = lambda d: (
    '        <sbitLineMetrics direction="%s"><ascender value="57"/><descender value="-14"/><widthMax value="%d"/>'
    '<caretSlopeNumerator value="0"/><caretSlopeDenominator value="0"/><caretOffset value="0"/><minOriginSB value="0"/>'
    '<minAdvanceSB value="0"/><maxBeforeBL value="0"/><minAfterBL value="0"/><pad1 value="0"/><pad2 value="0"/></sbitLineMetrics>' % (d, BMP_W))
cblc = ['<?xml version="1.0" encoding="UTF-8"?>', '<ttFont>', '  <CBLC>', '    <header version="3.0"/>', '    <strike index="0">', '      <bitmapSizeTable>',
        line_metrics("hori"), line_metrics("vert"),
        '        <colorRef value="0"/><startGlyphIndex value="%d"/><endGlyphIndex value="%d"/>' % (first_id, last_id),
        '        <ppemX value="%d"/><ppemY value="%d"/><bitDepth value="32"/><flags value="1"/>' % (PPEM, PPEM),
        '      </bitmapSizeTable>',
        '      <eblc_index_sub_table_1 imageFormat="17" firstGlyphIndex="%d" lastGlyphIndex="%d">' % (first_id, last_id)]
cblc += ['        <glyphLoc id="%d" name="%s"/>' % (i, order[i]) for i in range(first_id, last_id + 1)]
cblc += ['      </eblc_index_sub_table_1>', '    </strike>', '  </CBLC>', '</ttFont>']

with tempfile.TemporaryDirectory() as tmp:
    base = os.path.join(tmp, "base.ttf")
    fb.save(base)
    # One file for both tables: the index needs the offsets of the data.
    open(os.path.join(tmp, "bitmaps.ttx"), "w").write("\n".join(lines[:-1] + cblc[2:]))
    subprocess.run(["ttx", "-q", "-m", base, "-o", out_path, os.path.join(tmp, "bitmaps.ttx")], check=True)

print("images: %d, ligature rules: %d, blank glyphs: %d, glyphs: %d" % (len(files), len(rules), len(blank), len(order)))
print("wrote", out_path, os.path.getsize(out_path), "bytes")
