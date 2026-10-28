"""Load the committed gazetteer."""

import json
import re
from importlib.resources import files

from cockup.place import BBox, Place
from cockup.rudeness import RudenessKnob

_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_ZOOM_MIN = 8
_ZOOM_MAX = 18


class CatalogError(ValueError):
    """The shipped gazetteer is internally inconsistent."""


def load_catalog() -> tuple[Place, ...]:
    raw = json.loads((files(__package__) / "data" / "places.json").read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise CatalogError("places.json must be a non-empty list")
    places = tuple(_parse(item, index) for index, item in enumerate(raw))
    seen: dict[str, int] = {}
    dupes: list[str] = []
    for place in places:
        if place.id in seen:
            dupes.append(place.id)
        seen[place.id] = seen.get(place.id, 0) + 1
    if dupes:
        raise CatalogError(f"duplicate place ids: {sorted(set(dupes))}")
    return places


def _parse(item: object, index: int) -> Place:
    if not isinstance(item, dict):
        raise CatalogError(f"place {index} is not an object")
    ident = item.get("id", index)
    try:
        return _place_from(item)
    except CatalogError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise CatalogError(f"place {ident!r} is invalid: {exc}") from exc


def _place_from(item: dict) -> Place:
    ident = _text(item, "id")
    if not _ID.fullmatch(ident):
        raise CatalogError(f"place id {ident!r} must be a lowercase slug")
    name = _text(item, "name")
    lat = _coord(item, "lat", -90, 90)
    lon = _coord(item, "lon", -180, 180)
    zoom = item.get("zoom")
    if isinstance(zoom, bool) or not isinstance(zoom, (int, float)):
        raise CatalogError(f"{ident}: zoom must be a number")
    zoom_f = float(zoom)
    if not _ZOOM_MIN <= zoom_f <= _ZOOM_MAX:
        raise CatalogError(f"{ident}: zoom {zoom} is outside {_ZOOM_MIN}..{_ZOOM_MAX}")
    bbox = _bbox(item, ident)
    if not bbox.contains(lat, lon):
        raise CatalogError(f"{ident}: point ({lat}, {lon}) is outside bbox {tuple(bbox)}")
    country = _text(item, "country")
    if len(country) != 2 or not country.isalpha() or country != country.upper():
        raise CatalogError(f"{ident}: country must be an upper-case alpha-2 code")
    rudeness_raw = item.get("rudeness")
    if isinstance(rudeness_raw, bool) or not isinstance(rudeness_raw, int):
        raise CatalogError(f"{ident}: rudeness must be an int 0..5")
    try:
        rudeness = RudenessKnob(rudeness_raw)
    except ValueError as exc:
        raise CatalogError(f"{ident}: rudeness must be an int 0..5") from exc
    source = _text(item, "source")
    if not source.startswith(("https://www.openstreetmap.org/", "https://www.wikidata.org/")):
        raise CatalogError(f"{ident}: source must be an OpenStreetMap or Wikidata URL")
    return Place(
        id=ident,
        name=name,
        lat=lat,
        lon=lon,
        zoom=zoom_f,
        bbox=bbox,
        country=country,
        region=_text(item, "region"),
        rudeness=rudeness,
        note=_text(item, "note"),
        source=source,
    )


def _text(item: dict, key: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CatalogError(f"{item.get('id', '?')}: {key} must be a non-empty string")
    return value


def _coord(item: dict, key: str, low: float, high: float) -> float:
    value = item.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CatalogError(f"{item.get('id', '?')}: {key} must be a number")
    number = float(value)
    if not low <= number <= high:
        raise CatalogError(f"{item.get('id', '?')}: {key} {number} is outside {low}..{high}")
    return number


def _bbox(item: dict, ident: str) -> BBox:
    raw = item.get("bbox")
    if not isinstance(raw, list) or len(raw) != 4:
        raise CatalogError(f"{ident}: bbox must be [west, south, east, north]")
    numbers: list[float] = []
    for edge in raw:
        if isinstance(edge, bool) or not isinstance(edge, (int, float)):
            raise CatalogError(f"{ident}: bbox edges must be numbers")
        numbers.append(float(edge))
    west, south, east, north = numbers
    if west > east or south > north:
        raise CatalogError(f"{ident}: bbox is inside-out")
    return BBox(west, south, east, north)
