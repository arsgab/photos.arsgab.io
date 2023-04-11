from jinja2 import Environment
from pelican import signals, ArticlesGenerator

from markup import renderer_ref
from utils.staticfiles import get_static_url


GLOBALS = {
    'static': get_static_url,
}


def setup_jinja_env(generator: ArticlesGenerator) -> Environment:
    generator.env.globals.update(GLOBALS)
    renderer_ref.set(generator.env)
    return generator.env


def register() -> None:
    signals.article_generator_preread.connect(setup_jinja_env)
    signals.page_generator_preread.connect(setup_jinja_env)
