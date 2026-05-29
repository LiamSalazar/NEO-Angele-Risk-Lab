"""Asteroid identity value objects."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class AsteroidIdentity:
    """Stable identifiers and human-readable names for one small body."""

    object_key: str | None = None
    spkid: str | None = None
    des: str | None = None
    full_name: str | None = None
    name: str | None = None
    orbit_class_code: str | None = None
    orbit_class_name: str | None = None

    def best_identifier(self) -> str:
        """Return the most stable non-empty identifier available."""
        for value in (self.object_key, self.spkid, self.des, self.full_name, self.name):
            if _present(value):
                return str(value)
        return "unknown-object"

    def display_name(self) -> str:
        """Return the most useful label for UI, reports, and explanations."""
        for value in (self.name, self.full_name, self.des, self.spkid, self.object_key):
            if _present(value):
                return str(value)
        return "Unknown object"

    def to_dict(self) -> dict[str, str | None]:
        """Serialize to a plain dictionary."""
        return asdict(self)


def _present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() not in {"", "nan", "none", "null"}
    return True
