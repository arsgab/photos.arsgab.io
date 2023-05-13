import hashlib
from collections.abc import Iterable
from functools import cache
from json import dumps as json_dumps, loads as json_loads
from random import choice as rand_choice
from string import ascii_lowercase

from pelicanconf import STATIC_ASSETS_PATH, STATIC_BUILD_PATH, STATIC_URL

STATIC_MANIFEST = STATIC_BUILD_PATH / 'manifest.json'
ALLOWED_INLINE_SUFFIXES = {'.css', '.js', '.json'}


def get_static_url(filename: str, randomize: bool = True) -> str:
    filename = filename.strip('/')
    hashed_filename = get_staticfiles_manifest().get(filename)
    if hashed_filename:
        filename = hashed_filename
    elif randomize:
        filename = f'{filename}?v={get_random_string()}'
    return f'{STATIC_URL}{filename}'


def inline_static_assets(pattern: str) -> str:
    contents = get_staticfiles_contents(pattern)
    return '\n'.join(contents).strip() or ''


def get_random_string(length: int = 8) -> str:
    return ''.join(rand_choice(ascii_lowercase) for _ in range(length))


def get_staticfiles_contents(pattern: str) -> Iterable[str]:
    staticfiles = STATIC_ASSETS_PATH.glob(pattern)
    files = filter(lambda file: file.suffix in ALLOWED_INLINE_SUFFIXES, staticfiles)
    return [file.read_text() for file in files]


@cache
def get_staticfiles_manifest() -> dict[str, str]:
    if not STATIC_MANIFEST.is_file():
        return {}
    manifest_text = STATIC_MANIFEST.read_text()
    try:
        return json_loads(manifest_text)
    except ValueError:
        return {}


def generate_staticfiles_manifest(hash_digest_size: int = 10) -> dict[str, str]:
    manifest = {}
    files = (f.resolve() for f in STATIC_BUILD_PATH.glob('*') if f.suffix in {'.css', '.js'})
    for file in files:
        contents = file.read_bytes()
        hashstring = hashlib.blake2b(contents, digest_size=hash_digest_size).hexdigest()
        hashed_filename = f'{file.stem}.{hashstring}{file.suffix}'
        (STATIC_BUILD_PATH / hashed_filename).write_bytes(contents)
        manifest[file.name] = hashed_filename
    STATIC_MANIFEST.open('w').write(json_dumps(manifest))
    return manifest
