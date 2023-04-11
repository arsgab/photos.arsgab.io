from base64 import urlsafe_b64encode
from hashlib import sha256
from hmac import new as hmac_new
from textwrap import wrap
from typing import Any, Iterable, Iterator, NamedTuple, Optional

from pelicanconf import IMGPROXY_KEY, IMGPROXY_SALT, IMGPROXY_FQDN

assert bool(IMGPROXY_KEY), '`IMGPROXY_KEY` not set'
assert bool(IMGPROXY_SALT), '`IMGPROXY_SALT` not set'
KEY = bytes.fromhex(IMGPROXY_KEY)
SALT = bytes.fromhex(IMGPROXY_SALT)

MAX_IMAGE_WIDTH = 1400
DEFAULT_IMAGE_QUALITY = 80
BREAKPOINTS: tuple[int, ...] = (320, 480, 640, 800, 960, 1024, 1280)


def get_processed_image_url(
    source_url_or_path: str,
    ext: str = 'webp',
    encode: bool = True,
    **options: Any,
) -> str:
    if not source_url_or_path:
        return ''

    source_url = _qualify_source_image_url(source_url_or_path)
    source_url = _encode_source_image_url(source_url) if encode else f'plain/{source_url}'
    processing_options = '/'.join(
        f'{k}:{v}' for k, v in options.items() if v is not None
    )
    path = (
        f'/{processing_options}/{source_url}'
        if processing_options
        else f'/{source_url}'
    )
    if ext is not None:
        path = f'{path}.{ext}' if encode else f'{path}@{ext}'
    signature = _generate_image_path_signature(path).decode()
    return f'https://{IMGPROXY_FQDN}/{signature}{path}'


def get_resized_image_url(
    source_url: str, max_width: int, ext: str = 'webp', **extra: Any
) -> str:
    return get_processed_image_url(source_url, w=max_width, ext=ext, **extra)


class ImageResize(NamedTuple):
    width: int
    srcset: str
    condition: str = 'max-width'
    previous: Optional['ImageResize'] = None

    @property
    def media_query(self) -> str:
        return f'({self.condition}: {self.width}px)'

    @property
    def media_query_full(self) -> str:
        if self.previous:
            return (
                f'(min-width: {self.previous.width + 1}px) '
                f'and ({self.condition}: {self.width}px)'
            )
        return self.media_query

    @classmethod
    def get_defaults(
        cls,
        source_url: str,
        source_width: int = 9999,
        factors: Iterable[int] = (2,),
        scale: int = 1,
        **extra: Any,
    ) -> Iterator['ImageResize']:
        last_resize = None
        for width in BREAKPOINTS:
            if source_width < width:
                break
            params = {
                **extra,
                'q': extra.get('q') or DEFAULT_IMAGE_QUALITY
            }
            # Use max. quality for threshold small/large images
            if width < 480 or width > 1024:
                params.update(q=100)
            srcset = (
                get_resized_image_url(source_url, max_width=width * scale, **params),
                *cls._get_factors(
                    source_url, source_width, width * scale, factors or (), **params
                ),
            )
            last_resize = ImageResize(width, ', '.join(srcset), previous=last_resize)
            yield last_resize

        srcset = (
            get_resized_image_url(source_url, max_width=MAX_IMAGE_WIDTH * scale, **extra),
            *cls._get_factors(
                source_url,
                source_width,
                MAX_IMAGE_WIDTH * scale,
                factors or (),
                **extra,
            ),
        )
        yield ImageResize(
            last_resize.width + 1 if last_resize else 1,
            ', '.join(srcset),
            condition='min-width',
        )

    @staticmethod
    def _get_factors(
        source_url: str,
        source_width: int,
        width: int,
        factors: Iterable[int],
        **extra: Any,
    ) -> Iterator[str]:
        for factor in factors:
            extra_width = width * factor
            if source_width > extra_width:
                src = get_resized_image_url(source_url, max_width=extra_width, **extra)
                yield f'{src} {factor}x'

    @classmethod
    def get_fallback(cls, source_url: str, max_width: int = 1200, **kwargs: Any) -> str:
        return get_resized_image_url(source_url, max_width=max_width, **kwargs)


def _qualify_source_image_url(source_url: str) -> str:
    if source_url.startswith('http'):
        return source_url
    return f'local:///{source_url}'


def _encode_source_image_url(source_url: str) -> str:
    source_url = urlsafe_b64encode(source_url.encode()).rstrip(b'=')
    return '/'.join(wrap(source_url.decode(), 16))


def _generate_image_path_signature(path: str) -> bytes:
    digest = hmac_new(KEY, msg=SALT + path.encode(), digestmod=sha256).digest()
    return urlsafe_b64encode(digest).rstrip(b'=')

