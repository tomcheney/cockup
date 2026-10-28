"""A real place the map can fall back to."""

from dataclasses import dataclass
from typing import Any, NamedTuple

from cockup.rudeness import RudenessKnob


class BBox(NamedTuple):
    """West, south, east, north. Same order as a GeoJSON bbox."""

    west: float
    south: float
    east: float
    north: float

    def contains(self, lat: float, lon: float) -> bool:
        return self.west <= lon <= self.east and self.south <= lat <= self.north


@dataclass(frozen=True, slots=True)
class Place:
    """One gazetteer entry, framed for a web map."""

    id: str
    name: str
    lat: float
    lon: float
    zoom: float
    bbox: BBox
    country: str
    region: str
    rudeness: RudenessKnob
    note: str
    source: str

    def to_geojson(self) -> dict[str, Any]:
        """A GeoJSON Feature. Coordinates are ``[longitude, latitude]``."""
        return {
            "type": "Feature",
            "id": self.id,
            "bbox": [self.bbox.west, self.bbox.south, self.bbox.east, self.bbox.north],
            "geometry": {
                "type": "Point",
                "coordinates": [self.lon, self.lat],
            },
            "properties": {
                "name": self.name,
                "country": self.country,
                "region": self.region,
                "rudeness": self.rudeness.slug,
                "zoom": _json_number(self.zoom),
                "note": self.note,
            },
        }

    def to_dict(self) -> dict[str, Any]:
        """JSON-ready place, including the GeoJSON feature."""
        return {
            "id": self.id,
            "name": self.name,
            "lat": self.lat,
            "lon": self.lon,
            "zoom": _json_number(self.zoom),
            "bbox": [self.bbox.west, self.bbox.south, self.bbox.east, self.bbox.north],
            "country": self.country,
            "region": self.region,
            "rudeness": self.rudeness.slug,
            "note": self.note,
            "source": self.source,
            "geojson": self.to_geojson(),
        }


def _json_number(value: float) -> int | float:
    if value == int(value):
        return int(value)
    return value
