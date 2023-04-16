from contextlib import suppress
from html.parser import HTMLParser
from os.path import splitext
from re import compile as re_compile, Pattern
from xml.etree.ElementTree import Element, fromstring

from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension

from utils import ImageDimensions, ImageResize, render_template_partial, StrEnum


class Picture(HTMLParser):
    TAG: str = 'pic'
    DEFAULT_EXT: str = '.jpeg'
    DEFAULT_RATIO: float = 1.777  # 16:9
    attrs: dict[str, str] | None = None
    index: int = 1

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
        rendered = render_template_partial('picture', self.get_context())
        return fromstring(rendered)

    def get_context(self) -> dict:
        img_base, img_ext = splitext(self.attrs['src'])
        src = img_base + (img_ext or self.DEFAULT_EXT)
        eager = self.attrs.get('lazy') == 'false' or 'eager' in self.attrs
        ratio = self._get_ratio()
        dimensions = ImageDimensions.get_by_ratio(ratio)
        alt = self.attrs.get('alt') or f'Image {self.index}'
        columns, offset = self.attrs.get('grid', '|').split('|')
        columns = self.attrs.get('w') or columns
        offset = self.attrs.get('x') or offset
        return {
            'index': self.index,
            'sources': tuple(ImageResize.get_defaults(src)),
            'fallback': ImageResize.get_fallback(src),
            'loading': self.Loading.EAGER if eager else self.Loading.LAZY,
            'dimensions': dimensions,
            'ratio': ratio,
            'alt': alt,
            'src': src,
            'caption': self.attrs.get('caption', ''),
            'columns': columns or '*',
            'offset': offset or '*',
        }

    def _get_ratio(self) -> float:
        if self.attrs.get('orient') == self.Orientation.PORTRAIT:
            return round(1 / self.DEFAULT_RATIO, 2)
        ratio = self.attrs.get('ratio')
        if ratio and ':' in ratio:
            width, height = ratio.split(':')
            with suppress(ValueError):
                return int(width) / int(height)
        elif ratio:
            with suppress(ValueError):
                return float(ratio)
        return self.DEFAULT_RATIO


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
        return True


class PictureExtension(Extension):
    def extendMarkdown(self, md) -> None:
        md.parser.blockprocessors.register(PictureBlockProcessor(md.parser), 'pic', 999)


def makeExtension(**kwargs) -> PictureExtension:  # noqa
    return PictureExtension(**kwargs)
