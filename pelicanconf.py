from os import environ as env
from pathlib import Path


AUTHOR = env.get('AUTHOR')
SITENAME = env.get('SITENAME') or 'ag•photos'
TIMEZONE = env.get('TIMEZONE', 'Europe/Belgrade')
DEFAULT_DATE = 'fs'
STATS_SCRIPTS_URL = 'https://stat.arsgab.io/stonks.js'
STATS_WEBSITE_ID = env.get('STATS_WEBSITE_ID')

# Disable category/author/feeds pages build
CATEGORY_SAVE_AS = AUTHOR_SAVE_AS = ''
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
DISPLAY_PAGES_ON_MENU = DISPLAY_CATEGORIES_ON_MENU = False

# Build setup
DELETE_OUTPUT_DIRECTORY = env.get('DELETE_OUTPUT_DIRECTORY') == 'true'
DIRECT_TEMPLATES = ['index']
PATH = 'articles'
ARTICLE_SAVE_AS = PAGE_SAVE_AS = '{slug}.html'
ARTICLE_URL = PAGE_URL = '/{slug}'
OUTPUT_PATH = 'dist'
THEME = 'assets'
THEME_TEMPLATES_OVERRIDES = [f'{THEME}/scripts']
THEME_STATIC_PATHS = ['favicons', 'manifest.webmanifest']
THEME_STATIC_DIR = 'static'
PLUGIN_PATHS = ['markup']
PLUGINS = ['renderers']
STATIC_PATHS = []
BASE_DIR = Path('.')
STATIC_BUILD_DIR = BASE_DIR / OUTPUT_PATH / THEME_STATIC_DIR
STATIC_URL = f'/{THEME_STATIC_DIR}/'

# Processors/renderers setup
MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.meta': {},
        'markup.processors.picture': {},
    },
    'output_format': 'html5',
}

# Media processing setup
IMGPROXY_KEY = env.get('IMGPROXY_KEY')
IMGPROXY_SALT = env.get('IMGPROXY_SALT')
IMGPROXY_FQDN = env.get('IMGPROXY_FQDN', 'img.arsgab.io')
