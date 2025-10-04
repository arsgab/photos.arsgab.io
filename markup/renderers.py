from json import dumps as json_dumps
from random import randint
from uuid import uuid4

from jinja2 import Environment
from pelican import ArticlesGenerator, signals
from pelican.contents import Article

from markup import renderer_ref
from markup.processors.picture import Picture, get_picture_context, render_picture_tag
from pelicanconf import DATAFILES_PATH
from utils.datastructures import (
    dict_to_css_variables,
    get_geodata_from_articles,
    get_geodata_from_dataset,
)
from utils.media import get_processed_image_url
from utils.staticfiles import get_static_url, inline_static_assets
from utils.templating import (
    format_article_date_period,
    get_articles_colors_list,
    render_page_metadata,
    wrap_bullets,
)
from utils.url import get_datafile_url, qualify_url

GLOBALS = {
    'random': randint,
    'uuid': uuid4,
    'static': get_static_url,
    'api': get_datafile_url,
    'static_inline': inline_static_assets,
    'picture': render_picture_tag,
    'img': get_processed_image_url,
    'pagemeta': render_page_metadata,
    'colors': get_articles_colors_list,
    'article_date_period': format_article_date_period,
}

FILTERS = {
    'qualify': qualify_url,
    'cssvars': dict_to_css_variables,
    'bulletify': wrap_bullets,
}

POINTS_GEOJSON = DATAFILES_PATH / 'points.json'
LOCATIONS_GEOJSON = DATAFILES_PATH / 'locations.json'


def setup_jinja_env(generator: ArticlesGenerator) -> Environment:
    generator.env.globals.update(GLOBALS)
    generator.env.filters.update(FILTERS)
    renderer_ref.set(generator.env)
    return generator.env


def update_article_context(article_generator: ArticlesGenerator, content: Article) -> None:
    ctx = get_picture_context()
    if not ctx:
        return
    key, *_ = ctx.keys()
    pictures = ctx.pop(key)
    json_ld = Picture.create_json_ld(pictures)
    content.json_ld = list(json_ld)


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
