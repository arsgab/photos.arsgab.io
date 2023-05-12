from random import randint

from jinja2 import Environment
from pelican import ArticlesGenerator, signals
from pelican.contents import Article

from markup import renderer_ref
from markup.processors.picture import Picture, picture_processor_context_ref, render_picture_tag
from utils.staticfiles import get_static_url, inline_static_assets
from utils.templating import render_page_metadata
from utils.url import qualify_url

GLOBALS = {
    'random': randint,
    'static': get_static_url,
    'static_inline': inline_static_assets,
    'picture': render_picture_tag,
    'pagemeta': render_page_metadata,
}

FILTERS = {
    'qualify': qualify_url,
}


def setup_jinja_env(generator: ArticlesGenerator) -> Environment:
    generator.env.globals.update(GLOBALS)
    generator.env.filters.update(FILTERS)
    renderer_ref.set(generator.env)
    return generator.env


def update_article_context(article_generator: ArticlesGenerator, content: Article) -> None:
    picture_processor_context = picture_processor_context_ref.get()
    if not picture_processor_context:
        return
    key, *_ = picture_processor_context.keys()
    pictures = picture_processor_context.pop(key)
    json_ld = Picture.create_json_ld(pictures)
    setattr(content, 'json_ld', list(json_ld))


def register() -> None:
    signals.article_generator_preread.connect(setup_jinja_env)
    signals.page_generator_preread.connect(setup_jinja_env)
    signals.article_generator_write_article.connect(update_article_context)
