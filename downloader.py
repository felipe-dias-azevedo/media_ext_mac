import tempfile
import os
import shutil
import yt_dlp
import imageio_ffmpeg
from user_defaults import Normalization

class Downloader:
    def __init__(self, logger):
        self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        self.logger = logger

    def download(self, url: str, normalization: str) -> str:
        """Download best audio only as MP3, no metadata, no thumbnail"""

        normalization_map = { # TODO: check if these makes sense
            Normalization.LOW.value: "loudnorm=I=-16:TP=-1.5:LRA=11",
            Normalization.MEDIUM.value: "loudnorm=I=-14:TP=-1.0:LRA=7",
            Normalization.HIGH.value: "loudnorm=I=-13:TP=-1.0:LRA=6",
        }

        with tempfile.TemporaryDirectory(delete=False) as tmpdir:
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'logger': self.logger,
                'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '0',
                }],
                'ffmpeg_location': self.ffmpeg_path,
                'postprocessor_args': {
                    'ffmpeg': ['-af', normalization_map[normalization]],
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
            
            raise FileNotFoundError("Downloaded file not found")

        
    def move_file(self, src_path: str, dest_path: str):
        """Move a file from src_path to dest_path, overwriting if needed."""
        
        shutil.move(src_path, dest_path)
        shutil.rmtree(os.path.dirname(src_path), ignore_errors=True)
        return dest_path