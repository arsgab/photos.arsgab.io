from collections import defaultdict, deque
from collections.abc import Iterable, Iterator
from contextlib import suppress
from contextvars import ContextVar
from html.parser import HTMLParser
from re import Pattern, compile as re_compile
from typing import Any
from xml.etree.ElementTree import Element, fromstring as xml_from_string

from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension

from pelicanconf import AUTHOR
from utils import (
    ImageDimensions,
    ImageResizeSet,
    StrEnum,
    get_processed_image_url,
    render_template_partial,
)

PICTURE_DEFAULT_RATIO = 1.777  # 16:9
PICTURE_RATIO_PRECISION = 3
PICTURE_JSON_LD_BASE = {
    "@context": "https://schema.org/",
    "@type": "ImageObject",
    "creator": {"@type": "Person", "name": AUTHOR},
}
PICTURE_JSON_LD_MAX_ITEMS = 10
picture_processor_context_ref: ContextVar[defaultdict[int, deque['Picture']]] = ContextVar(
    'picture_processor_context', default=defaultdict(deque)
)


class Picture(HTMLParser):
    TAG: str = 'pic'
    index: int = 1
    ratio: float = PICTURE_DEFAULT_RATIO
    dimensions: ImageDimensions
    resizes: ImageResizeSet
    attrs: dict[str, str]
    src: str

    class Loading(StrEnum):
        LAZY = 'lazy'
        EAGER = 'eager'

    class Orientation(StrEnum):
        LANDSCAPE = 'landscape'
        PORTRAIT = 'portrait'

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]) -> None:
        self.attrs = dict(attrs) if tag == self.TAG else {}

    def feed(self, data: str) -> None:
        super().feed(data)
        self.src = self.attrs.get('src')
        if not self.src:
            return

        # Extract dimensions from filename or create fake from predefined ratio
        dimensions = ImageDimensions.extract_from_filename(self.src)
        if dimensions:
            ratio = round(dimensions.width / dimensions.height, PICTURE_RATIO_PRECISION)
        else:
            ratio = self._extract_ratio_value()
            dimensions = ImageDimensions.fake_from_ratio(ratio)
        self.ratio = ratio
        self.dimensions = dimensions

        # Create image resizes set
        self.resizes = self.get_resizes()

    def _extract_ratio_value(self, precision: int = PICTURE_RATIO_PRECISION) -> float:
        ratio = self.attrs.get('ratio')
        if ratio and ':' in ratio:
            width, height = ratio.split(':')
            with suppress(ValueError):
                ratio_value = int(width) / int(height)
                return round(ratio_value, precision)
        elif ratio:
            with suppress(ValueError):
                return float(ratio)
        if self.attrs.get('orient') == self.Orientation.PORTRAIT:
            return round(1 / PICTURE_DEFAULT_RATIO, precision)
        return PICTURE_DEFAULT_RATIO

    def create_element(self) -> Element:
        rendered = render_template_partial('picture', self.get_context())
        return xml_from_string(rendered)

    def get_resizes(self) -> ImageResizeSet:
        processing_options = {}

        # Crop before processing
        crop_params = self.attrs.get('crop', '').split(':')[:3]
        if len(crop_params) == 2:
            width, height = crop_params
            processing_options.update(crop=f'{width}:{height}:nowe')
        elif len(crop_params) == 3:
            width, height, gravity = crop_params
            processing_options.update(crop=f'{width}:{height}:{gravity}')

        # `version` value for cache bustling
        version = self.attrs.get('v')
        if version:
            processing_options.update(cachebuster=f'v{version}')

        return ImageResizeSet(self.src, source_width=self.dimensions.width, **processing_options)

    def get_context(self) -> dict:
        eager = self.attrs.get('lazy') == 'false' or 'eager' in self.attrs
        fetch_priority = 'high' if self.index == 1 and eager else 'auto'
        span, offset = self.attrs.get('grid', '|').split('|')
        span = self.attrs.get('w') or span
        offset = self.attrs.get('x') or offset
        return {
            'src': self.src,
            'index': self.index,
            'id': self.html_id,
            'sources': self.resizes.sources,
            'fallback': self.resizes.fallback,
            'loading': self.Loading.EAGER if eager else self.Loading.LAZY,
            'fetch_priority': fetch_priority,
            'dimensions': self.dimensions,
            'ratio': self.ratio,
            'alt': self.html_alt,
            'caption': self.html_caption,
            'span': span or '*',
            'offset': offset or '*',
        }

    @property
    def html_id(self) -> str:
        return self.attrs.get('id') or str(self.index)

    @property
    def html_alt(self) -> str:
        return self.attrs.get('alt') or f'Image {self.index}'

    @property
    def html_caption(self) -> str:
        # TODO: optionally turn auto-captions on/off
        return f'<a href="#{self.html_id}" rel="bookmark">{self.index}</a>'

    @classmethod
    def create_json_ld(
        cls, pictures: Iterable['Picture'], max_items: int | None = PICTURE_JSON_LD_MAX_ITEMS
    ) -> Iterator[dict]:
        for index, picture in enumerate(pictures):
            if max_items is not None and index >= max_items:
                break
            url = picture.resizes.get_fallback(max_width=1000, ext='jpg', q=80)
            yield {**PICTURE_JSON_LD_BASE, 'contentUrl': url}


class PictureBlockProcessor(BlockProcessor):
    REGEX: Pattern = re_compile(r'\[pic(.+)]')
    _count: int = 0

    def test(self, parent: Element, block: str) -> bool:
        return bool(self.REGEX.match(block))

    def run(self, parent: Element, blocks: list[str]) -> bool:
        block = blocks.pop(0).replace('[', '<').replace(']', '>')
        picture = Picture()
        picture.feed(block)
        if not picture.src:
            return False

        self._count += 1
        picture.index = self._count
        parent.append(picture.create_element())
        picture.close()
        refs = picture_processor_context_ref.get()
        refs[id(self)].append(picture)
        return True


class PictureExtension(Extension):
    def extendMarkdown(self, md) -> None:
        md.parser.blockprocessors.register(PictureBlockProcessor(md.parser), 'pic', 999)


def makeExtension(**kwargs) -> PictureExtension:  # noqa
    return PictureExtension(**kwargs)


# TODO: refactor this block
def render_picture_tag(
    src: str,
    width: int,
    ratio: float = PICTURE_DEFAULT_RATIO,
    loading: str = 'lazy',
    fetch_priority: str = 'auto',
    alt: str = '',
    **kwargs: Any,
) -> str:
    height = int(width * ratio)
    source = {
        'srcset': [
            get_processed_image_url(src, width=width, height=height, **kwargs),
            get_processed_image_url(src, width=width * 2, height=height * 2, **kwargs) + ' 2x',
        ],
        'media_query': '(min-width: 0px)',
    }
    fallback = get_processed_image_url(src, width=width, height=height, ext='jpg', **kwargs)
    ctx = {
        'sources': (source,),
        'fallback': fallback,
        'loading': loading,
        'fetch_priority': fetch_priority,
        'ratio': ratio,
        'dimensions': (width, height),
        'alt': alt,
    }
    return render_template_partial('picture-tag', ctx)
