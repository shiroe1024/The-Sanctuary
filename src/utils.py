import re

def extract_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    Supports: standard, shorts, and shortened links.
    """
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None