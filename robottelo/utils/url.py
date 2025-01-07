from urllib.parse import urlparse


def is_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except (ValueError, AttributeError):
        return False
