# Config Layer — Agent Instructions

- Config classes are `@dataclass` subclasses of `ConfigBase`. They are frozen at runtime.
- Do **not** mutate config objects from outside the controller. Use `Controller.transaction()`.
- New fields must have a **default value**.
- Load new fields with `data.get("field", default)` in `_from_dict_data()` — **never** `data["field"]`.
- Add every new field to `_to_dict_data()`.
- Increment `VERSION` only for breaking persisted schema changes.
- When bumping `VERSION`, implement `_migrate_data(cls, data, from_version)`.
- Add a `CHANGELOG.md` entry whenever `VERSION` changes.
- Raise `ConfigError` (from `flow3r.core.config.abc.config`) for serialisation errors.

See `docs/agent/config-layer.md` for full details.

