from base64 import urlsafe_b64encode
from hashlib import sha256
from hmac import new as hmac_new
from os.path import splitext
from re import VERBOSE, compile as re_compile
from textwrap import wrap
from typing import Any, Iterable, Iterator, NamedTuple, Optional

from pelicanconf import (
    IMGPROXY_DEFAULT_QUALITY,
    IMGPROXY_FQDN,
    IMGPROXY_KEY,
    IMGPROXY_PLAIN_SOURCE_URL,
    IMGPROXY_SALT,
    IMGPROXY_URL_NAMESPACE as URL_NAMESPACE,
)

assert bool(IMGPROXY_KEY), '`IMGPROXY_KEY` not set'
assert bool(IMGPROXY_SALT), '`IMGPROXY_SALT` not set'
KEY = bytes.fromhex(IMGPROXY_KEY)
SALT = bytes.fromhex(IMGPROXY_SALT)

IMAGE_DEFAULT_EXT = '.jpeg'
MAX_IMAGE_WIDTH = 1400
MAX_SOURCE_WIDTH = 9999
DEFAULT_BREAKPOINTS: tuple[int, ...] = (320, 480, 640, 800, 960, 1024, 1280)
SIZED_IMAGE_FILENAME_PATTERN = re_compile(
    r'''
    ^(?P<base>.+)  # base, e.g. istanbul/IMG_1850
    \.(?P<width>\d+)x(?P<height>\d+)$  # {width}x{height}, e.g. 800x600
''',
    flags=VERBOSE,
)


def get_processed_image_url(
    source_url_or_path: str,
    encode_source_url: bool = not IMGPROXY_PLAIN_SOURCE_URL,
    ext: str = 'webp',
    **options: Any,
) -> str:
    if not source_url_or_path:
        return ''

    source_url = _qualify_source_image_url(source_url_or_path)
    if encode_source_url:
        source_url = _encode_source_image_url(source_url)
    else:
        source_url = f'plain/{source_url}'
    processing_options = '/'.join(f'{k}:{v}' for k, v in options.items() if v is not None)
    path = f'/{processing_options}/{source_url}' if processing_options else f'/{source_url}'
    if ext is not None:
        path = f'{path}.{ext}' if encode_source_url else f'{path}@{ext}'
    signature = _generate_image_path_signature(path).decode()
    return f'https://{IMGPROXY_FQDN}/{signature}{path}'


def get_resized_image_url(source_url: str, width: int, ext: str = 'webp', **extra: Any) -> str:
    return get_processed_image_url(source_url, w=width, ext=ext, **extra)


class ImageDimensions(NamedTuple):
    width: int = 0
    height: int = 0

    @classmethod
    def extract_from_filename(cls, filename: str) -> Optional['ImageDimensions']:
        match = SIZED_IMAGE_FILENAME_PATTERN.match(filename)
        if match is None:
            return
        matched_groups = match.groupdict()
        try:
            width = int(matched_groups['width'])
            height = int(matched_groups['height'])
        except ValueError:
            return
        return cls(width, height)

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
        if self.condition == 'any':
            return '(min-width: 0px)'
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
    source_width: int
    max_width: int
    sources: Iterable[ImageResize] = ()
    fallback: str | None = None

    def __init__(
        self,
        source_url: str,
        source_width: int | None = MAX_SOURCE_WIDTH,
        max_width: int | None = MAX_IMAGE_WIDTH,
        breakpoints: Iterable[int] | None = DEFAULT_BREAKPOINTS,
        **processing_options: Any,
    ):
        self.source_url = source_url
        self.source_width = source_width
        self.max_width = max_width
        self.sources = tuple(self.get_resizes(breakpoints=breakpoints, **processing_options))
        self.fallback = self.get_fallback(max_width=max_width, ext='jpg', **processing_options)

    def get_resizes(
        self,
        breakpoints: Iterable[int] | None = DEFAULT_BREAKPOINTS,
        factors: Iterable[int] = (2,),
        **processing_options: Any,
    ) -> Iterator[ImageResize]:
        factors = factors or ()
        quality = processing_options.pop('q', None) or IMGPROXY_DEFAULT_QUALITY
        params = {**processing_options, 'q': quality}

        # Single resized image source requested, no intermediate resizes
        if breakpoints is None:
            srcset = (
                get_resized_image_url(self.source_url, width=self.max_width, **params),
                *self._get_factors(self.max_width, factors, **params),
            )
            yield ImageResize(self.max_width, srcset, condition='any')
            return

        relevant_breakpoints = filter(lambda b: b < self.source_width, breakpoints)
        last_resize = None
        for bp in relevant_breakpoints:
            srcset = (
                get_resized_image_url(self.source_url, width=bp, **params),
                *self._get_factors(bp, factors, **params),
            )
            last_resize = ImageResize(bp, srcset, previous=last_resize)
            yield last_resize

        factored = self._get_factors(self.max_width, factors, **params)
        srcset = (
            get_resized_image_url(self.source_url, width=MAX_IMAGE_WIDTH, **params),
            *factored,
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
            factored_width = width * factor
            if self.source_width <= factored_width:
                continue
            src = get_resized_image_url(self.source_url, width=factored_width, **extra)
            yield f'{src} {factor}x'

    def get_fallback(self, max_width: int | None = MAX_IMAGE_WIDTH, **kwargs: Any) -> str:
        return get_resized_image_url(self.source_url, width=max_width, **kwargs)


def _qualify_source_image_url(source_url: str) -> str:
    img_base, img_ext = splitext(source_url)

    # It's not an extension, it's dimensions part...
    if img_ext and len(img_ext) > 5:
        img_base = f'{img_base}{img_ext}'
        img_ext = None

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
