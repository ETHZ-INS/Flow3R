import re

class PlaceholderFormatter:
    # Matches {name} or {name:format_spec}, where name is a simple identifier
    _pattern = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)(?::([^{}]*))?}")

    # Sentinels to protect escaped braces while we parse
    _L = "\x00__LBRACE__\x00"
    _R = "\x00__RBRACE__\x00"

    def __init__(self, template: str):
        self.template = template

    def _protect_escaped_braces(self, s: str) -> str:
        # Replace {{ and }} with sentinels so they won't be matched as placeholders
        return s.replace("{{", self._L)[::-1].replace("}}", self._R)[::-1]

    def _restore_escaped_braces(self, s: str) -> str:
        # Bring back literal braces
        return s.replace(self._L, "{")[::-1].replace(self._R, "}")[::-1]

    def get_placeholders(self) -> set:
        """
        Return the set of placeholder names present in the template.
        Ignores malformed/unclosed placeholders and escaped braces.
        """
        protected = self._protect_escaped_braces(self.template)
        return {m.group(1) for m in self._pattern.finditer(protected)}

    def format(self, **kwargs) -> str:
        """
        Substitute placeholders with provided values.
        - Missing values are left as-is (e.g., "{unknown}" stays "{unknown}").
        - Malformed/unclosed placeholders are left untouched.
        - Supports Python format specs, e.g. "{x:.1f}", "{n:03}".
        - Escaped braces "{{" and "}}" are preserved as literal "{" and "}".
        """

        def repl(match: re.Match) -> str:
            name = match.group(1)
            if name not in kwargs or kwargs[name] is None:
                # Leave untouched if value not provided
                return match.group(0)

            return match.group(0).format(**{name: kwargs[name]})

        protected = self._protect_escaped_braces(self.template)
        result = self._pattern.sub(repl, protected)
        return self._restore_escaped_braces(result)
