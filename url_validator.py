from re import compile
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class YtValidator:
    def __init__(self, url: str):
        self.url = url
        self.query = parse_qs(urlparse(url).query)
        self.url_regex = compile(r"^(https?://)?(([a-zA-Z0-9-]+\.)?youtube\.com|youtu\.be)/.+$")

    def is_valid_url(self):
        return bool(self.url_regex.match(self.url))
    
    def is_playlist(self):
        return 'list' in self.query
    
    def is_content(self):
        return 'v' in self.query

    def remove_playlist_from_query(url):
        parsed = urlparse(url)
        
        query = parse_qs(parsed.query)
        
        query.pop('list', None)
        
        new_query = urlencode(query, doseq=True)
        
        cleaned_url = urlunparse(parsed._replace(query=new_query))
        
        return cleaned_url