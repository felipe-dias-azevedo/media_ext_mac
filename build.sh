set -euo pipefail
FFMPEG_BIN="$(python - <<'PY'
import imageio_ffmpeg
print(imageio_ffmpeg.get_ffmpeg_exe())
PY
)"
echo "ffmpeg at: $FFMPEG_BIN"
mkdir -p Resources
cp "$FFMPEG_BIN" Resources/ffmpeg
chmod +x Resources/ffmpeg

pyinstaller --name MediaExtractor --windowed \
    --add-binary "Resources/ffmpeg:Resources" \
    --hidden-import=yt_dlp \
    --hidden-import=imageio_ffmpeg \
    main.py