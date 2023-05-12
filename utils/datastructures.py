from enum import Enum
from typing import Iterable, Iterator

from pelican.contents import Article

Coords = tuple[float, float]
PointData = tuple[Article, Coords]


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


def get_geodata_from_articles(articles: Iterable[Article]) -> dict:
    coordinates = extract_articles_coordinates(articles)
    geopoints = generate_geopoints(coordinates)
    return {
        'type': 'FeatureCollection',
        'features': tuple(geopoints),
    }


def generate_geopoints(
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


def extract_articles_coordinates(articles: Iterable[Article]) -> Iterator[PointData]:
    for article in articles:
        coords_meta = article.metadata.get('coords')
        if not coords_meta:
            continue
        for coords in parse_coords_metadata(coords_meta):
            yield article, coords


def parse_coords_metadata(metadata: str) -> Iterator[Coords]:
    meta_values = map(str.strip, metadata.split(';'))
    for value in meta_values:
        values = map(str.strip, value.split(','))
        coords = map(float, values)
        try:
            yield tuple(coords)
        except ValueError:
            continue
