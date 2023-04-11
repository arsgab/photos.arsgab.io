from random import choice as rand_choice
from string import ascii_lowercase

# Predefined by Pelikan
STATIC_URL = '/theme/'


def get_static_url(filename: str, randomize: bool = True) -> str:
    filename = filename.strip('/')
    url = f'{STATIC_URL}{filename}'
    if randomize:
        randomizer = get_random_string()
        return f'{url}?v={randomizer}'
    return url


def get_random_string(length: int = 8) -> str:
    return ''.join(rand_choice(ascii_lowercase) for _ in range(length))
