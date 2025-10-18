cp .venv/lib/python3.13/site-packages/imageio_ffmpeg/binaries/ffmpeg* Resources/ffmpeg

pyinstaller --name MediaExtractor --windowed \
    --add-binary "Resources/ffmpeg:Resources" \
    --hidden-import=yt_dlp \
    --hidden-import=imageio_ffmpeg \
    main.py