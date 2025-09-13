# media_ext_py

### Install dependencies

```sh
pip install -r requirements.txt
```

### Run (dev)

```sh
python main.py
```

### Build .app

```sh
cp .venv/lib/python3.13/site-packages/imageio_ffmpeg/binaries/ffmpeg* Resources/ffmpeg
```

```sh
pyinstaller --name MediaExtractor --windowed \
    --add-binary "Resources/ffmpeg:Resources" \
    --hidden-import=yt_dlp \
    --hidden-import=imageio_ffmpeg \
    main.py
```
