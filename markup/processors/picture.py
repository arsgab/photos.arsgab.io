from contextlib import suppress
from html.parser import HTMLParser
from os.path import splitext
from re import compile as re_compile, Pattern
from xml.etree.ElementTree import Element, fromstring

from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension

from markup.renderers import render_template_partial
from utils import get_processed_image_url, StrEnum


class Picture(HTMLParser):
    TAG: str = 'pic'
    DEFAULT_EXT: str = '.jpeg'
    DEFAULT_RATIO: float = 1.777
    attrs: dict[str, str] = None

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
        url = get_processed_image_url(src, ext='webp')
        eager = self.attrs.get('lazy') == 'false' or 'eager' in self.attrs
        ratio = self._get_ratio()
        return {
            'url': url,
            'loading': self.Loading.EAGER if eager else self.Loading.LAZY,
            'padding': round(100 / ratio, 2),
            **self.attrs,
        }

    def _get_ratio(self) -> float:
        if self.attrs.get('orient') == self.Orientation.PORTRAIT:
            return round(1 / self.DEFAULT_RATIO, 2)
        with suppress(ValueError, TypeError):
            return float(self.attrs.get('ratio'))
        return self.DEFAULT_RATIO


class PictureBlockProcessor(BlockProcessor):
    REGEX: Pattern = re_compile(r'\[pic(.+)]')

    def test(self, parent: Element, block: str) -> bool:
        return bool(self.REGEX.match(block))

    def run(self, parent: Element, blocks: list[str]) -> bool:
        block = blocks.pop(0).replace('[', '<').replace(']', '>')
        picture = Picture()
        picture.feed(block)
        if not picture.attrs.get('src'):
            return False
        parent.append(picture.create_element())
        picture.close()
        return True


class PictureExtension(Extension):
    def extendMarkdown(self, md) -> None:
        md.parser.blockprocessors.register(PictureBlockProcessor(md.parser), 'pic', 999)


def makeExtension(**kwargs) -> PictureExtension:  # noqa
    return PictureExtension(**kwargs)
