from base64 import urlsafe_b64encode
from hashlib import sha256
from hmac import new as hmac_new
from os.path import splitext
from textwrap import wrap
from typing import Any, Iterable, Iterator, NamedTuple, Optional

from pelicanconf import IMGPROXY_FQDN, IMGPROXY_KEY, IMGPROXY_SALT

assert bool(IMGPROXY_KEY), '`IMGPROXY_KEY` not set'
assert bool(IMGPROXY_SALT), '`IMGPROXY_SALT` not set'
KEY = bytes.fromhex(IMGPROXY_KEY)
SALT = bytes.fromhex(IMGPROXY_SALT)

URL_NAMESPACE = 'photos.arsgab.io'
IMAGE_DEFAULT_EXT = '.jpeg'
MAX_IMAGE_WIDTH = 1400
DEFAULT_IMAGE_QUALITY = 80
DEFAULT_BREAKPOINTS: tuple[int, ...] = (320, 480, 640, 800, 960, 1024, 1280)


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
    processing_options = '/'.join(f'{k}:{v}' for k, v in options.items() if v is not None)
    path = f'/{processing_options}/{source_url}' if processing_options else f'/{source_url}'
    if ext is not None:
        path = f'{path}.{ext}' if encode else f'{path}@{ext}'
    signature = _generate_image_path_signature(path).decode()
    return f'https://{IMGPROXY_FQDN}/{signature}{path}'


def get_resized_image_url(source_url: str, max_width: int, ext: str = 'webp', **extra: Any) -> str:
    return get_processed_image_url(source_url, w=max_width, ext=ext, **extra)


class ImageDimensions(NamedTuple):
    width: int = 0
    height: int = 0

    @classmethod
    def fake_from_ratio(cls, ratio: float) -> 'ImageDimensions':
        return cls(MAX_IMAGE_WIDTH, int(MAX_IMAGE_WIDTH / ratio))


class ImageResize(NamedTuple):
    width: int
    srcset: Iterable[str]
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


class ImageResizeSet:
    source_url: str
    source_width: int = 9999
    max_width: int = MAX_IMAGE_WIDTH
    sources: Iterable[ImageResize] = ()
    fallback: str | None = None

    def __init__(
        self,
        source_url: str,
        source_width: int = None,
        max_width: int = None,
        breakpoints: Iterable[int] = DEFAULT_BREAKPOINTS,
        **processing_options: Any,
    ):
        self.source_url = source_url
        self.source_width = source_width or self.source_width
        self.max_width = max_width or self.max_width
        self.sources = tuple(self.get_resizes(breakpoints=breakpoints, **processing_options))
        self.fallback = self.get_fallback(max_width=max_width)

    def get_resizes(
        self,
        breakpoints: Iterable[int] = DEFAULT_BREAKPOINTS,
        factors: Iterable[int] = (2,),
        scale: int = 1,
        **processing_options: Any,
    ) -> Iterator[ImageResize]:
        last_resize = None
        for width in breakpoints:
            if self.source_width < width:
                break
            params = {
                **processing_options,
                'q': processing_options.get('q') or DEFAULT_IMAGE_QUALITY,
            }
            # Use max. quality for threshold small/large images
            if width < 480 or width > 1024:
                params.update(q=100)
            srcset = (
                get_resized_image_url(self.source_url, max_width=width * scale, **params),
                *self._get_factors(width * scale, factors or (), **params),
            )
            last_resize = ImageResize(width, srcset, previous=last_resize)
            yield last_resize

        max_width = MAX_IMAGE_WIDTH * scale
        srcset = (
            get_resized_image_url(self.source_url, max_width=max_width, **processing_options),
            *self._get_factors(
                self.max_width * scale,
                factors or (),
                **processing_options,
            ),
        )
        yield ImageResize(
            last_resize.width + 1 if last_resize else 1,
            srcset,
            condition='min-width',
        )

    def _get_factors(
        self,
        width: int,
        factors: Iterable[int],
        **extra: Any,
    ) -> Iterator[str]:
        for factor in factors:
            extra_width = width * factor
            if self.source_width > extra_width:
                src = get_resized_image_url(self.source_url, max_width=extra_width, **extra)
                yield f'{src} {factor}x'

    def get_fallback(self, max_width: int | None = None, **kwargs: Any) -> str:
        return get_resized_image_url(self.source_url, max_width=max_width or 1200, **kwargs)


def _qualify_source_image_url(source_url: str) -> str:
    img_base, img_ext = splitext(source_url)
    source_url = img_base + (img_ext or IMAGE_DEFAULT_EXT)
    if source_url.startswith('http'):
        return source_url
    source_url = f'{URL_NAMESPACE}/{source_url}' if URL_NAMESPACE else source_url
    return f'local:///{source_url}'


def _encode_source_image_url(source_url: str) -> str:
    source_url = urlsafe_b64encode(source_url.encode()).rstrip(b'=')
    return '/'.join(wrap(source_url.decode(), 16))


def _generate_image_path_signature(path: str) -> bytes:
    digest = hmac_new(KEY, msg=SALT + path.encode(), digestmod=sha256).digest()
    return urlsafe_b64encode(digest).rstrip(b'=')
