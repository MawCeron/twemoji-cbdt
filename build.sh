#!/bin/sh
# Builds build/TwemojiCBDT.ttf from the Twemoji graphics at a pinned version.
set -eu
cd "$(dirname "$0")"

ARTWORK_TAG=v17.0.3
ARTWORK_COMMIT=b6b55fef1e8636b540a6d016a4729ca8cdf2e60b
# The artwork's version, plus one for each release of the font built from it.
VERSION=17.0.3.1

[ -d build/twemoji ] || git clone -q --depth 1 --branch "$ARTWORK_TAG" https://github.com/jdecked/twemoji.git build/twemoji
[ "$(git -C build/twemoji rev-parse HEAD)" = "$ARTWORK_COMMIT" ] || { echo "build/twemoji is not $ARTWORK_TAG" >&2; exit 1; }

python3 build_cbdt.py build/twemoji/assets/72x72 build/TwemojiCBDT.ttf "Twemoji CBDT" "$VERSION"
python3 check.py build/TwemojiCBDT.ttf
