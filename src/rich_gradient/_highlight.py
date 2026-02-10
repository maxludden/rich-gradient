"""Normalize highlight configuration into validated, typed rule objects.

Provides dataclasses and helpers that accept legacy highlight configuration
shapes and convert them into explicit, parsed forms for word and regex
highlighting.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, TypeAlias, Union

from rich.style import Style, StyleType

HighlightWordsType: TypeAlias = Union[
    Mapping[str, StyleType],
    Sequence[tuple[str | Sequence[str], StyleType, bool]],
]
HighlightRegexType: TypeAlias = Union[
    Mapping[str, StyleType],
    Sequence[tuple[str, StyleType, int]],
]


@dataclass(frozen=True)
class HighlightWords:
    """
    Declarative configuration for word-based highlighting.

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
    def _from_mapping(cls, config: Mapping[Any, Any]) -> list["HighlightWords"]:
        normalize = cls._normalize_words
        parse_payload = cls._parse_payload
        rules: list[HighlightWords] = []
        for words_spec, payload in config.items():
            words = normalize(words_spec)
            style, case_sensitive = parse_payload(payload)
            rules.append(cls(words=words, style=style, case_sensitive=case_sensitive))
        return rules

    @classmethod
    def _from_sequence(cls, config: Sequence[Any]) -> list["HighlightWords"]:
        parse_entry = cls._parse_entry
        rules: list[HighlightWords] = []
        for entry in config:
            words, style, case_sensitive = parse_entry(entry)
            rules.append(cls(words=words, style=style, case_sensitive=case_sensitive))
        return rules

    @classmethod
    def from_config(cls, config: Any) -> list["HighlightWords"]:
        """
        Normalize legacy highlight_words configuration into HighlightWords instances.

        Accepts all previously supported shapes:
        - Mapping[word(s), style | payload]
        - Sequence of tuples or dicts
        """
        if isinstance(config, HighlightWords):
            return [config]
        if isinstance(config, Sequence) and not isinstance(config, (str, bytes)):
            if all(isinstance(item, HighlightWords) for item in config):
                return list(config)
        if isinstance(config, Sequence) and not isinstance(config, (str, bytes)):
            if any(isinstance(item, HighlightWords) for item in config):
                if not all(isinstance(item, HighlightWords) for item in config):
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
    """
    Declarative configuration for regex-based highlighting.

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
        return isinstance(value, Sequence) and not isinstance(value, (str, bytes))

    @staticmethod
    def _normalize_pattern(pat: Any, flags: int = 0) -> re.Pattern[str]:
        if isinstance(pat, re.Pattern):
            return pat
        if pat is None:
            raise ValueError("Regex pattern cannot be None.")
        return re.compile(str(pat), flags=flags)

    @staticmethod
    def _parse_payload(payload: Any) -> tuple[Style, int]:
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
    def _from_mapping(cls, config: Mapping[Any, Any]) -> list["HighlightRegex"]:
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
    def _from_sequence(cls, config: Sequence[Any]) -> list["HighlightRegex"]:
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
    def from_config(cls, config: Any) -> list["HighlightRegex"]:
        """
        Normalize legacy highlight_regex configuration into HighlightRegex instances.
        """
        if isinstance(config, HighlightRegex):
            return [config]
        if cls._is_sequence(config) and all(
            isinstance(item, HighlightRegex) for item in config
        ):
            return list(config)
        if cls._is_sequence(config):
            if any(isinstance(item, HighlightRegex) for item in config):
                if not all(isinstance(item, HighlightRegex) for item in config):
                    raise TypeError(
                        "Cannot mix HighlightRegex instances with legacy highlight configurations."
                    )

        if isinstance(config, Mapping):
            return cls._from_mapping(config)
        if cls._is_sequence(config):
            return cls._from_sequence(config)
        raise TypeError("highlight_regex must be a mapping or sequence.")
