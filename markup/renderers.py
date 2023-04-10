from jinja2.filters import do_mark_safe
from pelican import signals, ArticlesGenerator

from markup import renderer_ref

__all__ = ('render_template', 'render_template_partial', 'renderer_ref')


def render_template(template_name: str, ctx: dict = None) -> str:
    if not template_name.endswith('.html'):
        template_name = f'{template_name}.html'
    ctx = ctx or {}
    renderer = renderer_ref.get()
    template = renderer.get_template(template_name)
    rendered = template.render(ctx)
    return do_mark_safe(rendered)


def render_template_partial(partial_name: str, ctx: dict = None) -> str:
    return render_template(f'partials/{partial_name}', ctx=ctx)


def _get_pelikan_jinja_env(generator: ArticlesGenerator) -> None:
    renderer_ref.set(generator.env)


def register() -> None:
    signals.article_generator_init.connect(_get_pelikan_jinja_env)
