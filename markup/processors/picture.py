from collections import defaultdict, deque
from collections.abc import Iterable, Iterator
from contextlib import suppress
from contextvars import ContextVar
from html.parser import HTMLParser
from re import Pattern, compile as re_compile
from xml.etree.ElementTree import Element, fromstring

from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension

from pelicanconf import AUTHOR
from utils import ImageDimensions, ImageResizeSet, StrEnum, render_template_partial

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
    DEFAULT_EXT: str = '.jpeg'
    DEFAULT_RATIO: float = 1.777  # 16:9
    attrs: dict[str, str] | None = None
    index: int = 1
    resizes: ImageResizeSet

    class Loading(StrEnum):
        LAZY = 'lazy'
        EAGER = 'eager'

    class Orientation(StrEnum):
        LANDSCAPE = 'landscape'
        PORTRAIT = 'portrait'

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]) -> None:
        if tag == self.TAG:
            self.attrs = dict(attrs)

    def create_element(self) -> Element:
        self.resizes = ImageResizeSet(self.attrs['src'])
        rendered = render_template_partial('picture', self.get_context())
        return fromstring(rendered)

    def get_context(self) -> dict:
        idx = self.attrs.get('id') or self.index
        # TODO: optionally turn auto-captions on/off
        caption = f'<a href="#{idx}" rel="bookmark">{self.index}</a>'
        eager = self.attrs.get('lazy') == 'false' or 'eager' in self.attrs
        ratio = self._get_ratio()
        dimensions = ImageDimensions.fake_from_ratio(ratio)
        alt = self.attrs.get('alt') or f'Image {self.index}'
        columns, offset = self.attrs.get('grid', '|').split('|')
        columns = self.attrs.get('w') or columns
        offset = self.attrs.get('x') or offset
        return {
            'index': self.index,
            'id': idx,
            'sources': self.resizes.sources,
            'fallback': self.resizes.fallback,
            'loading': self.Loading.EAGER if eager else self.Loading.LAZY,
            'dimensions': dimensions,
            'ratio': ratio,
            'alt': alt,
            'src': self.attrs['src'],
            'caption': caption,
            'columns': columns or '*',
            'offset': offset or '*',
        }

    def _get_ratio(self) -> float:
        ratio = self.attrs.get('ratio')
        if ratio and ':' in ratio:
            width, height = ratio.split(':')
            with suppress(ValueError):
                return int(width) / int(height)
        elif ratio:
            with suppress(ValueError):
                return float(ratio)
        if self.attrs.get('orient') == self.Orientation.PORTRAIT:
            return round(1 / self.DEFAULT_RATIO, 3)
        return self.DEFAULT_RATIO

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
        if not picture.attrs.get('src'):
            return False
        self._count += 1
        picture.index = self._count
        parent.append(picture.create_element())
        picture.close()
        picture_processor_context_ref.get()[id(self)].append(picture)
        return True


class PictureExtension(Extension):
    def extendMarkdown(self, md) -> None:
        md.parser.blockprocessors.register(PictureBlockProcessor(md.parser), 'pic', 999)


def makeExtension(**kwargs) -> PictureExtension:  # noqa
    return PictureExtension(**kwargs)


def render_picture_tag(
    src: str, max_width: int | None = None, breakpoints: Iterable[int] | None = None, **kwargs
) -> str:
    resizes = ImageResizeSet(src, max_width=max_width, breakpoints=breakpoints, **kwargs)
    ctx = {
        'sources': resizes.sources,
        'fallback': resizes.fallback,
    }
    return render_template_partial('picture-tag', ctx)
