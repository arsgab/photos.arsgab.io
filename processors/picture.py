from html.parser import HTMLParser
from re import compile as re_compile, Pattern
from xml.etree.ElementTree import Element, SubElement

from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension


class Picture(HTMLParser):
    attrs: dict[str, str] = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str]]) -> None:
        if tag == 'pic':
            self.attrs = dict(attrs)

    def create_element(self, parent: Element) -> SubElement:
        # TODO: render template, create SubElement from string
        return SubElement(parent, 'ag-picture', attrib=self.attrs)


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
