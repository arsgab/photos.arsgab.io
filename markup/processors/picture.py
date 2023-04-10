from html.parser import HTMLParser
from re import compile as re_compile, Pattern
from xml.etree.ElementTree import Element, fromstring

from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension

from ..renderers import render_template_partial


class Picture(HTMLParser):
    attrs: dict[str, str] = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]) -> None:
        if tag == 'pic':
            self.attrs = dict(attrs)

    def create_element(self, parent: Element) -> Element:
        rendered = render_template_partial('picture', self.attrs)
        element = fromstring(rendered)
        parent.append(element)
        return element


class PictureBlockProcessor(BlockProcessor):
    REGEX: Pattern = re_compile(r'\[pic(.+)]')

    def test(self, parent: Element, block: str) -> bool:
        return bool(self.REGEX.match(block))

    def run(self, parent: Element, blocks: list[str]) -> None:
        block = blocks.pop(0).replace('[', '<').replace(']', '>')
        picture = Picture()
        picture.feed(block)
        picture.create_element(parent)
        picture.close()


class PictureExtension(Extension):
    def extendMarkdown(self, md) -> None:
        md.parser.blockprocessors.register(PictureBlockProcessor(md.parser), 'pic', 999)


def makeExtension(**kwargs) -> PictureExtension:  # noqa
    return PictureExtension(**kwargs)
