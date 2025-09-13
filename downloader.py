import tempfile
import os
import shutil
import yt_dlp
import imageio_ffmpeg

def download(url: str, logger) -> str:
    """Download best audio only as MP3, no metadata, no thumbnail"""

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    with tempfile.TemporaryDirectory(delete=False) as tmpdir:
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'logger': logger,
            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0',
            }],
            'ffmpeg_location': ffmpeg_path,
            'postprocessor_args': {
                'ffmpeg': ['-af', 'loudnorm=I=-13:TP=-1.0:LRA=6'],
            },
            'addmetadata': False,
            'writethumbnail': False,
            'embedthumbnail': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        for file in os.listdir(tmpdir):
            if file.endswith('.mp3'):
                return os.path.join(tmpdir, file)
        
        logger.error("Downloaded file not found")
        raise FileNotFoundError("Downloaded file not found")

    
def move_file(src_path: str, dest_path: str):
    """Move a file from src_path to dest_path, overwriting if needed."""
    
    shutil.move(src_path, dest_path)
    shutil.rmtree(os.path.dirname(src_path), ignore_errors=True)
    return dest_path