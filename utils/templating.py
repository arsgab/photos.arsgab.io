from random import shuffle as random_shuffle
from typing import Iterable, Iterator, NamedTuple

from jinja2 import pass_context
from jinja2.filters import do_mark_safe
from jinja2.runtime import Context
from pelican.contents import Article

from markup import renderer_ref
from pelicanconf import DEFAULT_OG_IMAGE, SITEDESC, SITENAME

from .media import get_processed_image_url

OG_IMAGE_WIDTH = 1200
OG_IMAGE_HEIGHT = 630
OG_IMAGE_PROCESSING_PARAMS = {
    'width': OG_IMAGE_WIDTH,
    'height': OG_IMAGE_HEIGHT,
    'ext': 'jpg',
    'gravity': 'so',
    'rt': 'fill',
    'q': 75,
}


def render_template(template_name: str, ctx: dict = None) -> str:
    renderer = renderer_ref.get()
    if not template_name.endswith('.html'):
        template_name = f'{template_name}.html'
    ctx = ctx or {}
    template = renderer.get_template(template_name)
    rendered = template.render(ctx)
    return do_mark_safe(rendered)


def render_template_partial(partial_name: str, ctx: dict = None) -> str:
    return render_template(f'partials/{partial_name}', ctx=ctx)


class PageMetadata(NamedTuple):
    title: str = SITENAME
    description: str = SITEDESC
    canonical_link: str | None = None
    og_type: str = 'website'
    og_title: str = SITENAME
    og_description: str = SITEDESC
    og_image: str = DEFAULT_OG_IMAGE
    og_image_width: int = OG_IMAGE_WIDTH
    og_image_height: int = OG_IMAGE_HEIGHT
    published_date: str | None = None

    @property
    def og_image_url(self) -> str:
        return get_processed_image_url(self.og_image, **OG_IMAGE_PROCESSING_PARAMS)

    @classmethod
    def from_context(cls, ctx: Context) -> 'PageMetadata':
        article = ctx.get('article')
        if not article:
            return cls()

        title = getattr(article, 'meta_title', '') or article.title
        description = getattr(article, 'meta_description', '')
        description = description or getattr(article, 'subtitle', '') or SITEDESC
        og_title = getattr(article, 'og_title', '') or title
        og_description = getattr(article, 'og_desc', '') or description
        og_image = getattr(article, 'og_image', '') or DEFAULT_OG_IMAGE
        return cls(
            title=title,
            description=description,
            canonical_link=article.url,
            og_type='article',
            og_title=og_title,
            og_description=og_description,
            og_image=og_image,
            published_date=article.date.strftime('%Y-%m-%d'),
        )


@pass_context
def render_page_metadata(ctx: Context) -> str:
    metadata = PageMetadata.from_context(ctx)
    return render_template_partial('pagemeta', {'meta': metadata})


@pass_context
def get_articles_colors_list(ctx: Context, shuffle: bool = False) -> list[str]:
    articles = ctx.get('articles') or ()
    colors = list(set(extract_all_articles_colors(articles)))
    if shuffle:
        random_shuffle(colors)
    return colors


def extract_all_articles_colors(articles: Iterable[Article]) -> Iterator[str]:
    for article in articles:
        color = article.metadata.get('color')
        if color:
            yield color.lower()
