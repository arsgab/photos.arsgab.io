from os import environ as env


AUTHOR = env.get('AUTHOR')
SITENAME = env.get('SITENAME')
TIMEZONE = env.get('TIMEZONE', 'Europe/Belgrade')

# Disable category/author/feeds pages build
CATEGORY_SAVE_AS = AUTHOR_SAVE_AS = ''
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Build setup
DIRECT_TEMPLATES = ['index']
PATH = 'articles'
OUTPUT_PATH = 'dist/'
THEME = 'assets'
