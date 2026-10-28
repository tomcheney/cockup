"""Selection, seeding, and GeoJSON."""

import json

import pytest

from cockup import NoPlaceError, RudenessKnob, fallback, places


def test_readme_sketch_returns_a_framed_place():
    session_id = "session-123"
    place = fallback(rudeness=RudenessKnob.STAG_DO, seed=session_id, country="GB")
    assert place.country == "GB"
    assert place.rudeness is RudenessKnob.STAG_DO
    assert isinstance(place.name, str) and place.name
    assert place.bbox.contains(place.lat, place.lon)


def test_seed_is_stable_and_decimal_strings_match_ints():
    kwargs = {"rudeness": RudenessKnob.RUGBY_TOUR, "country": "GB"}
    assert fallback(seed=42, **kwargs) == fallback(seed=42, **kwargs)
    assert fallback(seed=42, **kwargs) == fallback(seed="42", **kwargs)
    assert fallback(seed=42, **kwargs) == fallback(seed=b"42", **kwargs)


def test_different_seeds_can_land_on_different_places():
    seen = {
        fallback(rudeness=RudenessKnob.STAG_DO, country="GB", seed=seed).id
        for seed in range(12)
    }
    assert len(seen) > 1


def test_requested_tier_is_returned_when_the_country_has_it():
    place = fallback(rudeness="stag_do", seed="mast", country="gb")
    assert place.rudeness is RudenessKnob.STAG_DO
    assert place.country == "GB"


def test_uk_is_great_britain():
    kwargs = {"rudeness": 3, "seed": "session-123"}
    assert fallback(country="UK", **kwargs) == fallback(country="GB", **kwargs)
    assert all(place.country == "GB" for place in places(country="uk"))


def test_britain_steps_down_from_cancelled_to_rugby_tour():
    place = fallback(rudeness=RudenessKnob.CANCELLED, seed="race-1", country="GB")
    assert place.country == "GB"
    assert place.rudeness is RudenessKnob.RUGBY_TOUR
    assert place.id in {item.id for item in places(rudeness=RudenessKnob.RUGBY_TOUR, country="GB")}


def test_sparse_countries_step_down_without_leaving():
    france = fallback(rudeness="cancelled", country="FR", seed=1)
    assert france.id == "bitche"
    assert france.rudeness is RudenessKnob.RUGBY_TOUR
    denmark = fallback(rudeness=RudenessKnob.CANCELLED, country="DK", seed=1)
    assert denmark.id == "middelfart"
    assert denmark.rudeness is RudenessKnob.SCHOOL_RUN
    assert places(rudeness=RudenessKnob.CANCELLED, country="FR") == ()


def test_cancelled_in_the_united_states_does_not_step_down():
    place = fallback(rudeness=RudenessKnob.CANCELLED, country="US", seed="anywhere")
    assert place.id == "dickshooter"
    assert place.rudeness is RudenessKnob.CANCELLED


def test_unknown_country_is_an_error_rather_than_a_teleport():
    with pytest.raises(NoPlaceError) as caught:
        fallback(rudeness=RudenessKnob.STAG_DO, country="ZZ", seed=1)
    assert caught.value.country == "ZZ"
    assert places(country="ZZ") == ()


def test_malformed_country_and_rudeness_are_rejected():
    with pytest.raises(ValueError):
        fallback(country="Britain")
    with pytest.raises(ValueError):
        fallback(rudeness="filthy")
    with pytest.raises(TypeError):
        fallback(seed=True)


def test_geojson_feature_uses_longitude_latitude_order():
    place = fallback(rudeness=RudenessKnob.STAG_DO, seed="session-123", country="GB")
    feature = place.to_geojson()
    assert feature["type"] == "Feature"
    assert feature["id"] == place.id
    assert feature["geometry"] == {
        "type": "Point",
        "coordinates": [place.lon, place.lat],
    }
    assert feature["bbox"] == [place.bbox.west, place.bbox.south, place.bbox.east, place.bbox.north]
    assert feature["properties"]["name"] == place.name
    assert feature["properties"]["country"] == "GB"
    assert feature["properties"]["rudeness"] == "stag_do"
    assert feature["properties"]["zoom"] == int(place.zoom)
    assert feature["properties"]["note"] == place.note
    assert "source" not in feature["properties"]
    payload = place.to_dict()
    assert payload["geojson"] == feature
    assert payload["source"] == place.source
    json.dumps(payload)
