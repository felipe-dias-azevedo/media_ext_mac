from tui import get_tui, cprint
from downloader import download
from colors import *

class DownloaderLogger:
    def debug(self, msg):
        # yt-dlp sends a lot of "debug" messages here, including ffmpeg commands
        # if msg.startswith("[debug]"):
        #     return   # ignore debug spam
        cprint(f"[DEBUG] {msg}")

    def info(self, msg):
        cprint(f"{BLUE}[INFO] {msg}{EBLUE}")

    def warning(self, msg):
        cprint(f"{YELLOW}[WARNING] {msg}{EYELLOW}")

    def error(self, msg):
        cprint(f"{RED}[ERROR] {msg}{ERED}")


def handler(text: str):
    # cprint(f"{BLUE}You entered:{EBLUE}")
    cprint(f"{BOLD}{text}{EBOLD}")
    download(text, "audio", DownloaderLogger())
    
    # cprint(f"{RED}{'-'*40}{ERED}")
    # cprint(f"{RED}{'-'*40}{ERED}")

def main():
    get_tui(handler).run()

if __name__ == "__main__":
    main()