"""Pick a fallback place."""

import hashlib
import random

from cockup.catalog import load_catalog
from cockup.place import Place
from cockup.rudeness import RudenessKnob

_CATALOG: tuple[Place, ...] = load_catalog()


class NoPlaceError(LookupError):
    """No catalogue entry matched, even after stepping the rudeness down."""

    def __init__(self, rudeness: RudenessKnob, country: str | None) -> None:
        self.rudeness = rudeness
        self.country = country
        where = country or "any country"
        super().__init__(f"no place at or below {rudeness.slug} in {where}")


def fallback(
    rudeness: RudenessKnob | int | str = RudenessKnob.STAG_DO,
    *,
    seed: str | int | bytes | None = None,
    country: str | None = None,
) -> Place:
    """Return one real place at the requested setting of the rudeness knob.

    ``rudeness`` is how far you turned it. When that country has nothing
    at that setting, the next calmer setting in the same country is used,
    and so on. ``Place.rudeness`` is the setting you actually got.

    The same ``seed`` and filters always return the same place. ``seed=42``
    and ``seed="42"`` match. Omit ``seed`` for a different place each call.
    ``country`` is an ISO 3166-1 alpha-2 code; ``UK`` is accepted as ``GB``.
    Omit it to mean anywhere.
    """
    level = RudenessKnob.parse(rudeness)
    code = normalize_country(country)
    tier = level
    while True:
        eligible = _eligible(tier, code)
        if eligible:
            return _pick(eligible, seed)
        if tier is RudenessKnob.VICAR:
            raise NoPlaceError(level, code)
        tier = RudenessKnob(tier - 1)


def places(
    *,
    rudeness: RudenessKnob | int | str | None = None,
    country: str | None = None,
) -> tuple[Place, ...]:
    """Return catalogue entries for a tier and country, without stepping down.

    Omit either filter to leave it open. An unknown but well-formed country
    code returns an empty tuple.
    """
    level = None if rudeness is None else RudenessKnob.parse(rudeness)
    code = normalize_country(country)
    return tuple(
        place
        for place in _CATALOG
        if (level is None or place.rudeness is level) and (code is None or place.country == code)
    )


def normalize_country(country: str | None) -> str | None:
    """Return an alpha-2 code, or None for anywhere."""
    if country is None:
        return None
    if not isinstance(country, str):
        raise TypeError(f"country must be a str or None, got {type(country).__name__}")
    text = country.strip().upper()
    if not text:
        return None
    if text == "UK":
        text = "GB"
    if len(text) != 2 or not text.isalpha():
        raise ValueError(f"country must be an ISO 3166-1 alpha-2 code, got {country!r}")
    return text


def _eligible(tier: RudenessKnob, country: str | None) -> tuple[Place, ...]:
    return tuple(
        place
        for place in _CATALOG
        if place.rudeness is tier and (country is None or place.country == country)
    )


def _pick(eligible: tuple[Place, ...], seed: str | int | bytes | None) -> Place:
    if seed is None:
        return random.choice(eligible)
    material = _seed_bytes(seed)
    return max(eligible, key=lambda place: _score(material, place.id))


def _seed_bytes(seed: str | int | bytes) -> bytes:
    if isinstance(seed, bool) or not isinstance(seed, (str, int, bytes)):
        raise TypeError(f"seed must be str, int, bytes, or None, got {type(seed).__name__}")
    if isinstance(seed, bytes):
        return seed
    if isinstance(seed, str):
        return seed.encode("utf-8")
    return str(seed).encode("utf-8")


def _score(material: bytes, place_id: str) -> bytes:
    digest = hashlib.blake2s()
    digest.update(material)
    digest.update(b"\0")
    digest.update(place_id.encode("utf-8"))
    return digest.digest()
