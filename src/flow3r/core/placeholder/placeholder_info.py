from dataclasses import dataclass


@dataclass(frozen=True)
class PlaceholderInfo:
    """
    Lightweight descriptor for a single placeholder.

    ``name``  – the identifier used inside ``{...}`` in templates.
    ``label`` – a human-readable display name (e.g. for drag-and-drop UI).
    """

    name: str
    label: str

    def __str__(self) -> str:  # convenience
        return self.name

