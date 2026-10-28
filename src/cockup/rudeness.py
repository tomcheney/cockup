"""The rudeness knob.

Higher means a smuttier real place name.
"""

from enum import IntEnum


class RudenessKnob(IntEnum):
    """The rudeness knob. Higher means a smuttier real place name."""

    VICAR = 0
    SCHOOL_RUN = 1
    OFFICE_PARTY = 2
    STAG_DO = 3
    RUGBY_TOUR = 4
    CANCELLED = 5

    @property
    def slug(self) -> str:
        """Lower-case name used in JSON, query strings, and the CLI."""
        return self.name.lower()

    @property
    def label(self) -> str:
        return _LABELS[self]

    @property
    def description(self) -> str:
        return _DESCRIPTIONS[self]

    @classmethod
    def parse(cls, value: "RudenessKnob | int | str") -> "RudenessKnob":
        """Accept an enum member, an int 0–5, or a slug such as ``stag_do``."""
        if isinstance(value, cls):
            return value
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            raise TypeError(
                f"rudeness knob must be RudenessKnob, int, or str, got {type(value).__name__}"
            )
        if isinstance(value, int):
            try:
                return cls(value)
            except ValueError:
                pass
            raise ValueError(f"rudeness knob must be 0..5, got {value}")
        text = value.strip().lower().replace("-", "_").replace(" ", "_")
        if not text:
            raise ValueError("rudeness knob must not be empty")
        if text.isdigit() or (text[0] == "-" and text[1:].isdigit()):
            return cls.parse(int(text))
        for item in cls:
            if item.slug == text:
                return item
        known = ", ".join(item.slug for item in cls)
        raise ValueError(f"unknown rudeness knob {value!r}; expected one of {known}")


_LABELS: dict[RudenessKnob, str] = {
    RudenessKnob.VICAR: "Vicar",
    RudenessKnob.SCHOOL_RUN: "School run",
    RudenessKnob.OFFICE_PARTY: "Office party",
    RudenessKnob.STAG_DO: "Stag do",
    RudenessKnob.RUGBY_TOUR: "Rugby tour",
    RudenessKnob.CANCELLED: "Cancelled",
}

_DESCRIPTIONS: dict[RudenessKnob, str] = {
    RudenessKnob.VICAR: "Safe enough to say in front of the vicar.",
    RudenessKnob.SCHOOL_RUN: "Sayable on the school run, just.",
    RudenessKnob.OFFICE_PARTY: "Innuendo, once someone has opened the wine.",
    RudenessKnob.STAG_DO: "The mask slips.",
    RudenessKnob.RUGBY_TOUR: "Swearing, and nobody is writing it down.",
    RudenessKnob.CANCELLED: "No plausible denial. The booking would be cancelled.",
}
