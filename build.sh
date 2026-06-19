#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${GITHUB_REF_NAME:-}" ]]; then
    VERSION="${GITHUB_REF_NAME#v}"
else
    VERSION="$(git tag --sort=-version:refname | head -n 1)"
fi

pyinstaller --name MediaExt \
    --windowed \
    --icon icon.icns \
    --hidden-import=yt_dlp \
    --hidden-import=imageio_ffmpeg \
    --osx-bundle-identifier felipediasazevedo.mediaext \
    app.py

plutil -replace CFBundleShortVersionString \
    -string "$VERSION" \
    dist/MediaExt.app/Contents/Info.plist

codesign \
    --force \
    --deep \
    --sign - \
    dist/MediaExt.app
