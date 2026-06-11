pyinstaller --name MediaExt \
    --windowed \
    --icon icon.icns \
    --hidden-import=yt_dlp \
    --hidden-import=imageio_ffmpeg \
    --osx-bundle-identifier felipediasazevedo.mediaext \
    app.py
