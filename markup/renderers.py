from json import dumps as json_dumps
from random import randint

from jinja2 import Environment
from pelican import ArticlesGenerator, signals
from pelican.contents import Article

from markup import renderer_ref
from markup.processors.picture import Picture, picture_processor_context_ref, render_picture_tag
from pelicanconf import DATAFILES_PATH
from utils.datastructures import get_geodata_from_articles, get_geodata_from_dataset
from utils.staticfiles import get_static_url, inline_static_assets
from utils.templating import get_articles_colors_list, render_page_metadata
from utils.url import get_datafile_url, qualify_url

GLOBALS = {
    'random': randint,
    'static': get_static_url,
    'api': get_datafile_url,
    'static_inline': inline_static_assets,
    'picture': render_picture_tag,
    'pagemeta': render_page_metadata,
    'colors': get_articles_colors_list,
}

FILTERS = {
    'qualify': qualify_url,
}

POINTS_GEOJSON = DATAFILES_PATH / 'points.json'
LOCATIONS_GEOJSON = DATAFILES_PATH / 'locations.json'


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


def write_points_geojson(article_generator: ArticlesGenerator) -> None:
    geodata = get_geodata_from_articles(article_generator.articles)
    geojson = json_dumps(geodata, ensure_ascii=False)
    POINTS_GEOJSON.open('w').write(geojson)


def write_locations_geojson(*args) -> None:
    geodata = get_geodata_from_dataset()
    geojson = json_dumps(geodata, ensure_ascii=False)
    LOCATIONS_GEOJSON.open('w').write(geojson)


def register() -> None:
    signals.article_generator_preread.connect(setup_jinja_env)
    signals.page_generator_preread.connect(setup_jinja_env)
    signals.article_generator_write_article.connect(update_article_context)
    signals.article_generator_finalized.connect(write_points_geojson)
    signals.finalized.connect(write_locations_geojson)
