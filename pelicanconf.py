from os import environ as env
from pathlib import Path

from dotenv import load_dotenv

BASE_PATH = Path('.')
load_dotenv()

# Site setup
AUTHOR = env.get('AUTHOR')
SITENAME = env.get('SITENAME') or 'The Picture Is an Image'
SITE_FQDN = env.get('SITE_FQDN') or 'photos.arsgab.io'
SITEDESC = env.get('SITEDESC') or 'Personal photo archive'
TIMEZONE = env.get('TIMEZONE', 'Europe/Belgrade')
DEFAULT_DATE = 'fs'
STATS_SCRIPTS_URL = env.get('STATS_SCRIPTS_URL') or 'https://stat.arsgab.io/stonks'
STATS_WEBSITE_ID = env.get('STATS_WEBSITE_ID')
DEFAULT_OG_IMAGE = env.get('DEFAULT_OG_IMAGE') or 'share.png'

# Build setup
PATH = 'articles'
ARTICLE_SAVE_AS = PAGE_SAVE_AS = '{slug}.html'
ARTICLE_URL = PAGE_URL = '/{slug}'
OUTPUT_PATH = BASE_PATH / 'dist'
DIRECT_TEMPLATES = ['index']
THEME = 'assets'
THEME_TEMPLATES_OVERRIDES = [f'{THEME}/scripts']
THEME_STATIC_PATHS = ['favicons', 'manifest.webmanifest']
THEME_STATIC_DIR = 'static'
IGNORE_FILES = ['*.css']
PLUGIN_PATHS = ['markup']
PLUGINS = ['renderers']
DATAFILES_PATH = OUTPUT_PATH / 'data'
DATA_URL = '/data/'
LOAD_CONTENT_CACHE = env.get('LOAD_CONTENT_CACHE') == 'true'
DELETE_OUTPUT_DIRECTORY = env.get('DELETE_OUTPUT_DIRECTORY') == 'true'

# Create build directories
OUTPUT_PATH.mkdir(exist_ok=True)
DATAFILES_PATH.mkdir(exist_ok=True)

# Staticfiles
STATIC_PATHS = []
STATIC_ASSETS_PATH = BASE_PATH / THEME
STATIC_BUILD_PATH = OUTPUT_PATH / THEME_STATIC_DIR
STATIC_URL = f'/{THEME_STATIC_DIR}/'
INLINE_SCRIPTS = env.get('INLINE_SCRIPTS') == 'true'

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
IMGPROXY_DEFAULT_QUALITY = int(env.get('IMGPROXY_DEFAULT_QUALITY', '80'))
IMGPROXY_URL_SOURCE_FQDN = env.get('IMGPROXY_URL_SOURCE_FQDN')
IMGPROXY_URL_NAMESPACE = env.get('IMGPROXY_URL_NAMESPACE') or SITE_FQDN
IMGPROXY_PLAIN_SOURCE_URL = env.get('IMGPROXY_PLAIN_SOURCE_URL') == 'true'

# MapBox setup
MAPBOX_API_TOKEN = env.get('MAPBOX_API_TOKEN', '')

# Disable category/author/feeds pages build
CATEGORY_SAVE_AS = AUTHOR_SAVE_AS = ''
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None
DISPLAY_PAGES_ON_MENU = DISPLAY_CATEGORIES_ON_MENU = False
