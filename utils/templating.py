from typing import NamedTuple

from jinja2 import pass_context
from jinja2.filters import do_mark_safe
from jinja2.runtime import Context

from markup import renderer_ref
from pelicanconf import DEFAULT_OG_IMAGE, SITEDESC, SITENAME

from .media import get_resized_image_url

OG_IMAGE_WIDTH = 900


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
    og_type: str = 'website'
    og_title: str = SITENAME
    og_description: str = SITEDESC
    og_image: str = DEFAULT_OG_IMAGE

    @property
    def og_image_url(self) -> str:
        # TODO: force Telegram-prefered OG image proportions
        return get_resized_image_url(self.og_image, max_width=OG_IMAGE_WIDTH, ext='jpg', q=75)

    @classmethod
    def from_context(cls, ctx: Context) -> 'PageMetadata':
        article = ctx.get('article')
        if not article:
            return cls()

        title = getattr(article, 'meta_title', article.title)
        description = (
            getattr(article, 'meta_description', '') or getattr(article, 'subtitle', '') or SITEDESC
        )
        og_title = getattr(article, 'og_title', '') or title
        og_description = getattr(article, 'og_desc', '') or description
        og_image = getattr(article, 'og_image', '') or DEFAULT_OG_IMAGE
        return cls(
            title=title,
            description=description,
            og_type='article',
            og_title=og_title,
            og_description=og_description,
            og_image=og_image,
        )


@pass_context
def render_page_metadata(ctx: Context) -> str:
    metadata = PageMetadata.from_context(ctx)
    return render_template_partial('pagemeta', {'meta': metadata})
