from yarl import URL

from .setup_logging import setup_logging


def to_absolute_url(origin_url: URL, target_url: URL) -> URL:
    if target_url.is_absolute():
        return target_url
    else:
        origin_url = origin_url.origin()
        return origin_url.join(target_url)


def parse_urls_from_tag_attr(key: str, value: str) -> list[str]:
    if isinstance(value, list):
        return value
    else:
        if key.lower() == 'srcset':
            return [part.split()[0] for part in value.split(", ")]
        else:
            return [value]


__all__ = [
    'setup_logging',
    'to_absolute_url',
    'parse_urls_from_tag_attr'
]