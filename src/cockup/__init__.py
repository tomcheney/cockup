"""A fallback gazetteer of amusing real places, with a rudeness knob."""

from cockup.fallback import NoPlaceError, fallback, places
from cockup.place import BBox, Place
from cockup.rudeness import RudenessKnob

__all__ = [
    "BBox",
    "NoPlaceError",
    "Place",
    "RudenessKnob",
    "fallback",
    "places",
]

__version__ = "0.1.0"
