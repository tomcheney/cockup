"""The shipped gazetteer stays internally consistent."""

import subprocess
import sys

from cockup import RudenessKnob, places
from cockup.catalog import load_catalog


def test_import_does_not_load_the_web_stack():
    script = (
        "import cockup, sys; "
        "assert 'starlette' not in sys.modules; "
        "assert 'cockup.web' not in sys.modules"
    )
    subprocess.check_call([sys.executable, "-c", script])


def test_catalogue_is_a_full_gazetteer():
    catalogue = load_catalog()
    assert len(catalogue) >= 60
    assert len({place.id for place in catalogue}) == len(catalogue)


def test_every_place_is_framed_on_its_point():
    for place in load_catalog():
        assert place.bbox.contains(place.lat, place.lon)
        assert place.bbox.west <= place.lon <= place.bbox.east
        assert place.bbox.south <= place.lat <= place.bbox.north
        assert 8 <= place.zoom <= 18
        assert place.name.strip()
        assert place.note.strip()
        assert place.region.strip()
        assert len(place.country) == 2
        assert place.source.startswith(
            ("https://www.openstreetmap.org/", "https://www.wikidata.org/")
        )


def test_every_tier_has_places():
    for level in RudenessKnob:
        assert places(rudeness=level), level.slug


def test_britain_is_populated_through_rugby_tour():
    for level in (
        RudenessKnob.VICAR,
        RudenessKnob.SCHOOL_RUN,
        RudenessKnob.OFFICE_PARTY,
        RudenessKnob.STAG_DO,
        RudenessKnob.RUGBY_TOUR,
    ):
        assert places(rudeness=level, country="GB"), level.slug
    assert places(rudeness=RudenessKnob.CANCELLED, country="GB") == ()


def test_bbox_is_a_geojson_sequence():
    place = places(rudeness=RudenessKnob.STAG_DO, country="GB")[0]
    assert tuple(place.bbox) == (place.bbox.west, place.bbox.south, place.bbox.east, place.bbox.north)
