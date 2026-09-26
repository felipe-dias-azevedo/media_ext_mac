from re import compile as re_compile
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class YtValidator:

    _URL_RE = re_compile(r"^(https?://)?(([a-zA-Z0-9-]+\.)?youtube\.com|youtu\.be)/.+$")

    def __init__(self, url: str):
        self.url = url
        self.query = parse_qs(urlparse(url).query)

    def is_valid_url(self):
        return bool(self._URL_RE.match(self.url))

    def is_playlist(self):
        return "list" in self.query

    def is_content(self):
        return "v" in self.query

    @staticmethod
    def remove_playlist_from_query(url):
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        query.pop("list", None)
        new_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=new_query))