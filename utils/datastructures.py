from collections.abc import Iterable, Iterator
from enum import Enum
from tomllib import load as toml_load

from pelican.contents import Article

from pelicanconf import STATIC_ASSETS_PATH

Coords = tuple[float, float]
PointData = tuple[Article, Coords]

LOCATIONS_DATASET = STATIC_ASSETS_PATH / 'locations.toml'


def dict_to_css_variables(values: dict, only_values: bool = False) -> str:
    variables = '; '.join(f'--{var}: {value}' for var, value in values.items())
    return variables if only_values else f'style="{variables}"'


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


def get_geodata_from_articles(articles: Iterable[Article]) -> dict:
    coordinates = _extract_articles_coords(articles)
    geopoints = _generate_geopoints_from_articles_coords(coordinates)
    return {
        'type': 'FeatureCollection',
        'features': tuple(geopoints),
    }


def get_geodata_from_dataset() -> dict:
    with LOCATIONS_DATASET.open(mode='rb') as dataset_file:
        dataset = toml_load(dataset_file)
    geopoints = _generate_geopoints_from_dataset_items(dataset)
    return {
        'type': 'FeatureCollection',
        'features': tuple(geopoints),
    }


def _generate_geopoints_from_dataset_items(dataset: dict[str, dict]) -> Iterator[dict]:
    for location_name, location in dataset.items():
        coords = location.get('coords')
        if not coords:
            continue
        yield {
            'type': 'Feature',
            'properties': {
                'title': location.get('name') or location_name.title(),
                'year': location.get('year'),
            },
            'geometry': {
                'type': 'Point',
                'coordinates': list(reversed(coords)),
            },
        }


def _generate_geopoints_from_articles_coords(
    data: Iterable[PointData], default_point_color: str = 'grey'
) -> Iterator[dict]:
    for article, coords in data:
        yield {
            'type': 'Feature',
            'properties': {
                'title': article.title,
                'color': article.metadata.get('color') or default_point_color,
                'locationName': article.metadata.get('location'),
                'url': article.url,
            },
            'geometry': {
                'type': 'Point',
                'coordinates': coords,
            },
        }


def _extract_articles_coords(articles: Iterable[Article]) -> Iterator[PointData]:
    for article in articles:
        coords_meta = article.metadata.get('coords')
        if not coords_meta:
            continue
        for coords in _parse_coords_metadata(coords_meta):
            yield article, coords


def _parse_coords_metadata(metadata: str) -> Iterator[Coords]:
    meta_values = map(str.strip, metadata.split(';'))
    for value in meta_values:
        values = map(str.strip, value.split(','))
        coords = map(float, values)
        try:
            yield tuple(coords)
        except ValueError:
            continue
