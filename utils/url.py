from urllib.parse import urljoin

from pelicanconf import SITE_FQDN


def qualify_url(url: str, host: str = SITE_FQDN, scheme: str = 'https') -> str:
    if not url:
        return ''
    if url.startswith('http'):
        return url
    base = f'{scheme}://{host}'
    return urljoin(base, url)
