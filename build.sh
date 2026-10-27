#!/bin/sh
# Builds build/Twemoji.ttf from the Twemoji graphics at a pinned version.
set -eu
cd "$(dirname "$0")"

TAG=v17.0.3
COMMIT=b6b55fef1e8636b540a6d016a4729ca8cdf2e60b

[ -d build/twemoji ] || git clone -q --depth 1 --branch "$TAG" https://github.com/jdecked/twemoji.git build/twemoji
[ "$(git -C build/twemoji rev-parse HEAD)" = "$COMMIT" ] || { echo "build/twemoji is not $TAG" >&2; exit 1; }

python3 build_cbdt.py build/twemoji/assets/72x72 build/Twemoji.ttf Twemoji "${TAG#v}"
python3 check.py build/Twemoji.ttf
