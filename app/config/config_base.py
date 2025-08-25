from __future__ import annotations
from dataclasses import dataclass, field, fields
from typing import ClassVar, List, Final, Dict, Any, Type, TypeVar, Iterable

LOCK_SELF: Final[str] = "self"
LOCK_ALL:  Final[str] = "all"

T = TypeVar("T", bound="ConfigBase")

@dataclass
class ConfigBase:
    """
    A reusable mix-in that adds:

    * locked_values      – list[str] with keyword-only init
    * lock() / is_locked()
    * write protection via __setattr__
    """

    locked_values: List[str] = field(
        default_factory=list,
        kw_only=True,          # keeps it out of the positional args
        repr=False,            # hide from __repr__ if you prefer
    )

    # subclasses may add more allowed pseudo-names by extending this set
    _EXTRA_LOCK_NAMES: ClassVar[set[str]] = {LOCK_SELF, LOCK_ALL}

    def _verify_lock_names(self, names: Iterable[str]) -> None:
        """Verify that all names in locked_values are valid."""
        unknown = [n for n in names if n not in self._lockable_names()]
        if unknown:
            raise ValueError(f"Unknown lock targets for {type(self).__name__}: {unknown}")

    # ---------- helper API ----------
    def lock(self, *names: str) -> None:
        self._verify_lock_names(names)
        self.locked_values.extend(n for n in names if n not in self.locked_values)

    def unlock(self, *names: str) -> None:
        self._verify_lock_names(names)
        self.locked_values[:] = [n for n in self.locked_values if n not in names]

    def is_locked(self, name: str) -> bool:
        self._verify_lock_names([name])
        return LOCK_ALL in self.locked_values or name in self.locked_values

    # ---------- internals ----------
    def _lockable_names(self) -> set[str]:
        """Names that are legal arguments for lock()/unlock()."""
        return {f.name for f in fields(self)} | self._EXTRA_LOCK_NAMES

    def __setattr__(self, name, value):
        super().__setattr__(name, value)

    def to_dict(self) -> Dict[str, Any]:
        """Template method: gather child’s data + our locked_values."""
        data: Dict[str, Any] = self._extra_to_dict()
        if self.locked_values:                       # leave out if empty
            data["locked_values"] = self.locked_values
        return data

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Template method: let child parse its fields, we add locked_values."""
        kwargs = cls._extra_from_dict(data)
        kwargs["locked_values"] = data.get("locked_values", [])
        return cls(**kwargs)                         # type: ignore[arg-type]

    # ── hook methods for subclasses ------------------------------------------------
    def _extra_to_dict(self) -> Dict[str, Any]:
        """Override in subclasses; base returns nothing."""
        return {}

    @classmethod
    def _extra_from_dict(cls: Type[T], data: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclasses; base returns nothing."""
        return {}
