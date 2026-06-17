import tempfile
import os
import shutil
import yt_dlp
import imageio_ffmpeg
from user_defaults import Normalization
from utils import human_size
from re import compile

class Downloader:
    def __init__(self, logger, progresser):
        self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        self.logger = logger
        self.progresser = progresser

        self._seen_postprocessors = {}

        self.url_regex = compile("^(https?:\/\/)?(([a-zA-Z0-9-]+\.)?youtube\.com|youtu\.be)\/.+$")

    def _postprocessor(self, d):
        postprocessor = d.get("postprocessor")
        status = d.get("status")

        if status == "started":
            if postprocessor not in self._seen_postprocessors:
                self._seen_postprocessors[postprocessor] = False
                self.progresser.postprocess(f"Post Processing: {postprocessor}")

        elif status == "finished" and postprocessor in self._seen_postprocessors and not self._seen_postprocessors[postprocessor]:
            self.progresser.finish_postprocess(f"Post Processing: {postprocessor}")

    def _progress(self, d):
        if d.get("status") == "downloading":
            downloaded = d.get("downloaded_bytes", 0) or 0
            total = d.get("total_bytes", 1) or 1

            percentage = downloaded / total * 100
            speed = d.get("speed", 0) or 0
            elapsed = d.get("elapsed", 0) or 0

            msg = f"{percentage:.1f}% - {human_size(speed)}/s - Elapsed: {elapsed:.1f} seconds"

            self.progresser.download(msg)
        elif d.get("status") == "finished":
            total = d.get("total_bytes", 0) or 0
            elapsed = d.get("elapsed", 0) or 0
            self.progresser.finish_download(f"Size: {human_size(total)} - Elapsed: {elapsed:.1f} seconds")

    def download(self, url: str, normalization: str) -> str:
        """Download best audio only as MP3, no metadata, no thumbnail"""

        self._seen_postprocessors = {}

        normalization_map = {
            Normalization.LOW.value:    "loudnorm=I=-16:TP=-1.5:LRA=11",
            Normalization.MEDIUM.value: "loudnorm=I=-14:TP=-1.5:LRA=8",
            Normalization.HIGH.value:   "loudnorm=I=-12:TP=-1.5:LRA=6",
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
                    # '-id3v2_version': '3',
                },
                "addmetadata": True,
                "color": "never",
                'addmetadata': False,
                'writethumbnail': False,
                'embedthumbnail': False,
                'progress_hooks': [self._progress],
                'postprocessor_hooks': [self._postprocessor],
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
    
    def is_valid_url(self, url: str):
        return bool(self.url_regex.match(url))
