VERSION=$(git tag --sort=-version:refname | head -n 1)

pyinstaller --name MediaExt \
    --windowed \
    --icon icon.icns \
    --hidden-import=yt_dlp \
    --hidden-import=imageio_ffmpeg \
    --osx-bundle-identifier felipediasazevedo.mediaext \
    app.py

plutil -replace CFBundleShortVersionString -string "$VERSION" dist/MediaExt.app/Contents/Info.plist
