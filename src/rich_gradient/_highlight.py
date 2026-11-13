"""Normalize highlight configuration into validated, typed rule objects.

Provides dataclasses and helpers that accept legacy highlight configuration
shapes and convert them into explicit, parsed forms for word and regex
highlighting.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias

from rich.style import Style, StyleType

HighlightWordsType: TypeAlias = (
    Mapping[str, StyleType]
    | Sequence[tuple[str | Sequence[str], StyleType, bool]]
)
HighlightRegexType: TypeAlias = (
    Mapping[str, StyleType]
    | Sequence[tuple[str, StyleType, int]]
)


@dataclass(frozen=True)
class HighlightWords:
    """Declarative configuration for word-based highlighting.

    This class represents a normalized, validated highlight-word rule and
    replaces the loose HighlightWordsType union. It may be constructed
    directly or via the `from_config` classmethod for backward compatibility.

    Args:
        words (tuple[str, ...]): Tuple of words to highlight.
        style (Style): Style to apply to matched words.
        case_sensitive (bool): Whether matching is case-sensitive. Defaults to True.
    """

    words: tuple[str, ...]
    style: Style
    case_sensitive: bool = True

    @staticmethod
    def _normalize_words(words: Any) -> tuple[str, ...]:
        """Coerce a word specification into a non-empty tuple of strings.

        Args:
            words: A single word or a sequence of words.

        Returns:
            The words as a tuple, with empty strings dropped.

        Raises:
            ValueError: If a sequence contains no non-empty words.
            TypeError: If ``words`` is neither a string nor a sequence.
        """
        if isinstance(words, str):
            return (words,)
        if isinstance(words, Sequence) and not isinstance(words, (str, bytes)):
            normalized = tuple(str(w) for w in words if str(w))
            if not normalized:
                raise ValueError(
                    "Word sequences must contain at least one non-empty string."
                )
            return normalized
        raise TypeError("Highlight words must be a string or sequence of strings.")

    @staticmethod
    def _parse_payload(payload: Any) -> tuple[Style, bool]:
        """Parse the value side of a ``highlight_words`` mapping entry.

        Args:
            payload: A style, a ``(style[, case_sensitive])`` sequence, or a
                mapping with ``style`` and optional ``case_sensitive`` keys.

        Returns:
            The parsed style and the case-sensitivity flag (default ``True``).
        """
        if isinstance(payload, Mapping):
            style = payload.get("style")
            case_sensitive = bool(payload.get("case_sensitive", True))
        elif isinstance(payload, (list, tuple)):
            style = payload[0]
            case_sensitive = bool(payload[1]) if len(payload) > 1 else True
        else:
            style = payload
            case_sensitive = True
        return Style.parse(str(style)), case_sensitive

    @classmethod
    def _parse_entry(cls, entry: Any) -> tuple[tuple[str, ...], Style, bool]:
        """Parse one entry of a sequence-style ``highlight_words`` config.

        Args:
            entry: A ``(words, style[, case_sensitive])`` sequence or a mapping
                with ``words``, ``style`` and optional ``case_sensitive`` keys.

        Returns:
            The normalized words, parsed style, and case-sensitivity flag.

        Raises:
            TypeError: If ``entry`` is not a mapping or a non-string sequence.
            ValueError: If a sequence entry has fewer than two items.
        """
        normalize = cls._normalize_words
        parse_style = Style.parse

        if isinstance(entry, Mapping):
            words = normalize(entry["words"])
            style = entry["style"]
            case_sensitive = bool(entry.get("case_sensitive", True))
            return words, parse_style(str(style)), case_sensitive

        if not isinstance(entry, Sequence) or isinstance(entry, (str, bytes)):
            raise TypeError("Highlight word entries must be mappings or tuples/lists.")

        if len(entry) < 2:
            raise ValueError(
                "Highlight word tuples must be (words, style[, case_sensitive])."
            )

        words = normalize(entry[0])
        style = entry[1]
        case_sensitive = bool(entry[2]) if len(entry) > 2 else True
        return words, parse_style(str(style)), case_sensitive

    @classmethod
    def _from_mapping(cls, config: Mapping[Any, Any]) -> list[HighlightWords]:
        """Build rules from a ``{words: style | payload}`` mapping.

        Args:
            config: Mapping of word specifications to style payloads.

        Returns:
            One ``HighlightWords`` rule per mapping entry.
        """
        normalize = cls._normalize_words
        parse_payload = cls._parse_payload
        rules: list[HighlightWords] = []
        for words_spec, payload in config.items():
            words = normalize(words_spec)
            style, case_sensitive = parse_payload(payload)
            rules.append(cls(words=words, style=style, case_sensitive=case_sensitive))
        return rules

    @classmethod
    def _from_sequence(cls, config: Sequence[Any]) -> list[HighlightWords]:
        """Build rules from a sequence of tuple or mapping entries.

        Args:
            config: Sequence of entries accepted by ``_parse_entry``.

        Returns:
            One ``HighlightWords`` rule per entry.
        """
        parse_entry = cls._parse_entry
        rules: list[HighlightWords] = []
        for entry in config:
            words, style, case_sensitive = parse_entry(entry)
            rules.append(cls(words=words, style=style, case_sensitive=case_sensitive))
        return rules

    @classmethod
    def from_config(cls, config: Any) -> list[HighlightWords]:
        """Normalize legacy highlight_words configuration into HighlightWords instances.

        Accepts all previously supported shapes:

        - ``HighlightWords`` or a sequence of them (returned as-is)
        - ``Mapping[word(s), style | payload]``
        - Sequence of ``(words, style[, case_sensitive])`` tuples or dicts

        Args:
            config: The highlight-words configuration in any supported shape.

        Returns:
            The normalized list of ``HighlightWords`` rules.

        Raises:
            TypeError: If ``HighlightWords`` instances are mixed with legacy
                entries, or ``config`` is not a mapping or sequence.
            ValueError: If an entry is malformed (see ``_parse_entry``).
        """
        if isinstance(config, HighlightWords):
            return [config]
        if (
            isinstance(config, Sequence)
            and not isinstance(config, (str, bytes))
            and all(isinstance(item, HighlightWords) for item in config)
        ):
            return [item for item in config if isinstance(item, HighlightWords)]
        if (
            isinstance(config, Sequence)
            and not isinstance(config, (str, bytes))
            and any(isinstance(item, HighlightWords) for item in config)
            and not all(isinstance(item, HighlightWords) for item in config)
        ):
            raise TypeError(
                "Cannot mix HighlightWords instances with legacy highlight configurations."
            )

        if isinstance(config, Mapping):
            return cls._from_mapping(config)
        if isinstance(config, Sequence) and not isinstance(config, (str, bytes)):
            return cls._from_sequence(config)
        raise TypeError("highlight_words must be a mapping or sequence.")


@dataclass(frozen=True)
class HighlightRegex:
    """Declarative configuration for regex-based highlighting.

    Replaces HighlightRegexType and encapsulates pattern compilation
    and validation.

    Args:
        pattern (re.Pattern[str]): Compiled regex pattern to match.
        style (Style): Style to apply to matched text.
    """

    pattern: re.Pattern[str]
    style: Style

    @staticmethod
    def _is_sequence(value: Any) -> bool:
        """Return whether ``value`` is a sequence other than ``str``/``bytes``.

        Args:
            value: The object to test.

        Returns:
            ``True`` for non-string sequences, ``False`` otherwise.
        """
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes))

    @staticmethod
    def _normalize_pattern(pat: Any, flags: int = 0) -> re.Pattern[str]:
        """Compile a pattern specification into a regex.

        Args:
            pat: A compiled pattern (returned unchanged) or a pattern string.
            flags: ``re`` flags to compile with, e.g. ``re.IGNORECASE``. Ignored
                for compiled patterns. Defaults to 0.

        Returns:
            The compiled regular expression.

        Raises:
            ValueError: If ``pat`` is ``None``.
        """
        if isinstance(pat, re.Pattern):
            return pat
        if pat is None:
            raise ValueError("Regex pattern cannot be None.")
        return re.compile(str(pat), flags=flags)

    @staticmethod
    def _parse_payload(payload: Any) -> tuple[Style, int]:
        """Parse the value side of a ``highlight_regex`` mapping entry.

        Args:
            payload: A style, a ``(style[, flags])`` sequence, or a mapping
                with ``style`` and optional ``flags`` keys.

        Returns:
            The parsed style and the regex flags (default ``0``).
        """
        if isinstance(payload, Mapping):
            style = payload["style"]
            flags = int(payload.get("flags", 0))
        elif isinstance(payload, (list, tuple)):
            style = payload[0]
            flags = int(payload[1]) if len(payload) > 1 else 0
        else:
            style = payload
            flags = 0
        return Style.parse(str(style)), flags

    @classmethod
    def _parse_entry(cls, entry: Any) -> tuple[re.Pattern[str], Style]:
        """Parse one entry of a sequence-style ``highlight_regex`` config.

        Args:
            entry: A ``(pattern, style[, flags])`` sequence or a mapping with
                ``pattern``, ``style`` and optional ``flags`` keys.

        Returns:
            The compiled pattern and parsed style.

        Raises:
            TypeError: If ``entry`` is not a mapping or a non-string sequence.
            ValueError: If a sequence entry has fewer than two items.
        """
        normalize = cls._normalize_pattern
        parse_style = Style.parse

        if isinstance(entry, Mapping):
            pattern = normalize(entry["pattern"], int(entry.get("flags", 0)))
            style = entry["style"]
            return pattern, parse_style(str(style))

        if not isinstance(entry, Sequence) or isinstance(entry, (str, bytes)):
            raise TypeError("Highlight regex entries must be mappings or tuples/lists.")

        if len(entry) < 2:
            raise ValueError(
                "Highlight regex tuples must be (pattern, style[, flags])."
            )

        pattern = normalize(entry[0], int(entry[2]) if len(entry) > 2 else 0)
        style = entry[1]
        return pattern, parse_style(str(style))

    @classmethod
    def _from_mapping(cls, config: Mapping[Any, Any]) -> list[HighlightRegex]:
        """Build rules from a ``{pattern: style | payload}`` mapping.

        Args:
            config: Mapping of pattern specifications to style payloads.

        Returns:
            One ``HighlightRegex`` rule per mapping entry.
        """
        parse_payload = cls._parse_payload
        normalize = cls._normalize_pattern
        rules: list[HighlightRegex] = []
        for pattern_spec, payload in config.items():
            style, flags = parse_payload(payload)
            rules.append(
                cls(
                    pattern=normalize(pattern_spec, flags),
                    style=style,
                )
            )
        return rules

    @classmethod
    def _from_sequence(cls, config: Sequence[Any]) -> list[HighlightRegex]:
        """Build rules from a sequence of tuple or mapping entries.

        Args:
            config: Sequence of entries accepted by ``_parse_entry``.

        Returns:
            One ``HighlightRegex`` rule per entry.
        """
        parse_entry = cls._parse_entry
        rules: list[HighlightRegex] = []
        for entry in config:
            pattern, style = parse_entry(entry)
            rules.append(
                cls(
                    pattern=pattern,
                    style=style,
                )
            )
        return rules

    @classmethod
    def from_config(cls, config: Any) -> list[HighlightRegex]:
        """Normalize legacy highlight_regex configuration into HighlightRegex instances.

        Accepts all previously supported shapes:

        - ``HighlightRegex`` or a sequence of them (returned as-is)
        - ``Mapping[pattern, style | payload]``
        - Sequence of ``(pattern, style[, flags])`` tuples or dicts

        Args:
            config: The highlight-regex configuration in any supported shape.

        Returns:
            The normalized list of ``HighlightRegex`` rules.

        Raises:
            TypeError: If ``HighlightRegex`` instances are mixed with legacy
                entries, or ``config`` is not a mapping or sequence.
            ValueError: If an entry is malformed (see ``_parse_entry``).
        """
        if isinstance(config, HighlightRegex):
            return [config]
        if cls._is_sequence(config) and all(
            isinstance(item, HighlightRegex) for item in config
        ):
            return [item for item in config if isinstance(item, HighlightRegex)]
        if (
            cls._is_sequence(config)
            and any(isinstance(item, HighlightRegex) for item in config)
            and not all(isinstance(item, HighlightRegex) for item in config)
        ):
            raise TypeError(
                "Cannot mix HighlightRegex instances with legacy highlight configurations."
            )

        if isinstance(config, Mapping):
            return cls._from_mapping(config)
        if cls._is_sequence(config):
            return cls._from_sequence(config)
        raise TypeError("highlight_regex must be a mapping or sequence.")
