import hmac
from base64 import urlsafe_b64encode
from hashlib import sha256
from textwrap import wrap
from typing import Any
from pelicanconf import IMGPROXY_KEY, IMGPROXY_SALT, IMGPROXY_FQDN

assert bool(IMGPROXY_KEY), '`IMGPROXY_KEY` not set'
assert bool(IMGPROXY_SALT), '`IMGPROXY_SALT` not set'
KEY = bytes.fromhex(IMGPROXY_KEY)
SALT = bytes.fromhex(IMGPROXY_SALT)


def get_processed_image_url(
    source_url_or_path: str,
    ext: str = None,
    encode: bool = True,
    **options: Any,
) -> str:
    if not source_url_or_path:
        return ''

    source_url = qualify_source_url(source_url_or_path)
    source_url = encode_source_url(source_url) if encode else f'plain/{source_url}'
    processing_options = '/'.join(
        f'{k}:{v}' for k, v in options.items() if v is not None
    )
    path = (
        f'/{processing_options}/{source_url}'
        if processing_options
        else f'/{source_url}'
    )
    if ext is not None:
        path = f'{path}.{ext}' if encode_source_url else f'{path}@{ext}'
    signature = generate_signature(path).decode()
    return f'https://{IMGPROXY_FQDN}/{signature}{path}'


def qualify_source_url(source_url: str) -> str:
    if source_url.startswith('http'):
        return source_url
    return f'local:///{source_url}'


def encode_source_url(source_url: str) -> str:
    source_url = urlsafe_b64encode(source_url.encode()).rstrip(b'=')
    return '/'.join(wrap(source_url.decode(), 16))


def generate_signature(path: str) -> bytes:
    if not all((KEY, SALT)):
        return b'insecure'
    digest = hmac.new(KEY, msg=SALT + path.encode(), digestmod=sha256).digest()
    return urlsafe_b64encode(digest).rstrip(b'=')

