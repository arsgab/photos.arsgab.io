from random import choice as rand_choice
from string import ascii_lowercase

from pelicanconf import THEME_STATIC_DIR


def get_static_url(filename: str, randomize: bool = True) -> str:
    filename = filename.strip('/')
    url = f'/{THEME_STATIC_DIR}/{filename}'
    if randomize:
        randomizer = get_random_string()
        return f'{url}?v={randomizer}'
    return url


def get_random_string(length: int = 8) -> str:
    return ''.join(rand_choice(ascii_lowercase) for _ in range(length))
