import tempfile
import os
import shutil
import yt_dlp
import imageio_ffmpeg

def download(url: str, output_file: str, logger) -> str:
    """Download best audio only as MP3, no metadata, no thumbnail"""

    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    with tempfile.TemporaryDirectory() as tmpdir:
        
        temp_out = os.path.join(tmpdir, "audio")

        ydl_opts = {
            'format': 'bestaudio/best',
            'logger': logger,
            'outtmpl': temp_out + '.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '0',
            }],
            'ffmpeg_location': ffmpeg_path,
            'postprocessor_args': {
                'ffmpeg': ['-af', 'loudnorm=I=-16:TP=-1.5:LRA=11'],
            },
            'addmetadata': False,
            'writethumbnail': False,
            'embedthumbnail': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the normalized MP3
        temp_mp3 = temp_out + ".mp3"
        if not os.path.exists(temp_mp3):
            raise FileNotFoundError("yt-dlp did not produce an MP3")

        # Move to final location
        shutil.move(temp_mp3, output_file + ".mp3")

        return output_file + ".mp3"