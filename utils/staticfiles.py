from functools import cache
from json import loads as json_loads
from random import choice as rand_choice
from string import ascii_lowercase

from pelicanconf import STATIC_BUILD_DIR, STATIC_URL

STATIC_MANIFEST = STATIC_BUILD_DIR / 'manifest.json'


def get_static_url(filename: str, randomize: bool = True) -> str:
    filename = filename.strip('/')
    hashed_filename = get_staticfiles_manifest().get(filename)
    if hashed_filename:
        filename = hashed_filename
    elif randomize:
        filename = f'{filename}?v={get_random_string()}'
    return f'{STATIC_URL}{filename}'


def get_random_string(length: int = 8) -> str:
    return ''.join(rand_choice(ascii_lowercase) for _ in range(length))


@cache
def get_staticfiles_manifest() -> dict[str, str]:
    if not STATIC_MANIFEST.is_file():
        return {}
    manifest_text = STATIC_MANIFEST.read_text()
    try:
        return json_loads(manifest_text)
    except ValueError:
        return {}
