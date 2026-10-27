"""Checks a font built by build_cbdt.py: usage: check.py FONT.ttf"""
import sys

from fontTools.ttLib import TTFont

font = TTFont(sys.argv[1])
name = lambda i: font["name"].getDebugName(i)
cmap = font.getBestCmap()
cblc = font["CBLC"].strikes[0]
bitmaps = font["CBDT"].strikeData[0]

assert name(1) == "Twemoji", name(1)
assert 0x1F600 in cmap and cmap[0x1F600] in bitmaps, "U+1F600 has no image"
assert 0x200D in cmap and cmap[0x200D] not in bitmaps, "ZWJ must be a blank glyph"
assert "GSUB" in font and "glyf" not in font
assert len(bitmaps) >= 3000, len(bitmaps)
assert "creativecommons.org/licenses/by/4.0" in name(14), "license URL missing"
assert cblc.bitmapSizeTable.ppemX == 61

print("ok: %s, %d images, %d code points, %s" % (name(4), len(bitmaps), len(cmap), name(5)))
