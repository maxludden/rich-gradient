"""Pure-Python runtime configuration for rich-gradient (JSON file + env overrides)."""

from __future__ import annotations

import builtins
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

from loguru import logger

from rich.color import ColorParseError

from ._color_ext import install, is_installed, parse_color

if not is_installed():
    install()


def _deep_update(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively update base dict with override and return base (mutates base)."""
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v
    return base


_TRUTHY = ("1", "true", "yes", "on")
_FALSY = ("0", "false", "no", "off", "")


def _parse_bool(value: Any, *, default: bool, source: str) -> bool:
    """Interpret a config/env value as a boolean.

    Real booleans pass through, and strings use the same truthy values as the
    ``RICH_GRADIENT_ANIMATE`` environment variable. Anything unrecognised
    falls back to ``default`` with a warning instead of silently becoming
    ``False``.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUTHY:
            return True
        if lowered in _FALSY:
            return False
    logger.warning(f"Ignoring invalid boolean {value!r} from {source}")
    return default


def _clean_colors(candidate: Any, *, source: str) -> dict[str, str]:
    """Return only the usable ``name -> color`` entries from ``candidate``.

    Entries whose name or value is not a string, or whose value no color
    parser understands, are dropped with a warning. Without this a single bad
    entry in a config file would surface later as a confusing error the first
    time a ``Spectrum`` is built.
    """
    if not isinstance(candidate, dict):
        logger.warning(f"Ignoring colors from {source}: expected a JSON object")
        return {}
    cleaned: dict[str, str] = {}
    for name, value in candidate.items():
        if not isinstance(name, str) or not isinstance(value, str):
            logger.warning(f"Ignoring color {name!r}={value!r} from {source}")
            continue
        try:
            parse_color(value)
        except ColorParseError:
            logger.warning(f"Ignoring color {name!r}: {value!r} from {source} is invalid")
            continue
        cleaned[name] = value
    return cleaned


@dataclass
class Color:
    """Represents a color with a name and hex value."""

    name: str
    hex: str


@dataclass
class Colors:
    """Represents a collection of colors."""

    __root__: list[Color] = field(
        default_factory=lambda: [
            Color("red", "#FF0000"),
            Color("tomato", "#FF5500"),
            Color("orange", "#FF9900"),
            Color("gold", "#FFCC00"),
            Color("yellow", "#FFFF00"),
            Color("green", "#AAFF00"),
            Color("lime", "#00FF00"),
            Color("mint", "#00FF99"),
            Color("cyan", "#00FFFF"),
            Color("lightblue", "#00CCFF"),
            Color("skyblue", "#0099FF"),
            Color("blue", "#5066FF"),
            Color("purple", "#8055FF"),
            Color("violet", "#B033FF"),
            Color("magenta", "#FF00FF"),
            Color("pink", "#FF00AA"),
            Color("rose", "#FF0055"),
        ]
    )

    @property
    def names(self) -> list[str]:
        """Return a list of color names."""
        return [color.name for color in self.__root__]

    @property
    def hex(self) -> list[str]:
        """Return a list of color hex values."""
        return [color.hex for color in self.__root__]

    def as_dict(self) -> builtins.dict[str, str]:
        """Return a dictionary mapping color names to hex values."""
        return {color.name: color.hex for color in self.__root__}

    @property
    def dict(self) -> builtins.dict[str, str]:
        """Return a dictionary mapping color names to hex values."""
        return self.as_dict()


@dataclass(frozen=True)
class RichGradientConfig:
    """Runtime configuration for rich-gradient.

    Use RichGradientConfig.load(...) to create an instance. The loader will:
    - start from DEFAULT_CONFIG
    - merge a JSON config file if present (by default: ~/.rich-gradient/config.json)
    - apply environment variable overrides

    Attributes (public API):
        home_dir: Directory rich-gradient reads its config file from.
        animate: whether animations are enabled.
        colors: mapping of color-name -> hex value.
    """

    DEFAULT_CONFIG: ClassVar[dict] = {
        "rich-gradient-home-dir": str(Path.home() / ".rich-gradient"),
        "animate": True,
        "colors": Colors().as_dict(),
    }

    home_dir: Path
    animate: bool
    colors: dict

    @property
    def spectrum_colors(self) -> list[str]:
        """Return the spectrum colors as an ordered list of hex strings.

        Order follows the keys in the merged colors mapping. This is typically
        the default ordering unless overridden by a config file.
        """
        return list(self.colors.values())

    @property
    def animation_enabled(self) -> bool:
        """Whether rich-gradient should animate (use animated renderables).

        A shorthand property for templates that need to choose between animated
        and regular renderable versions.
        """
        return bool(self.animate)

    @classmethod
    def load(cls, config_path: Path | None = None) -> RichGradientConfig:
        """Load configuration.

        Precedence, lowest to highest: built-in defaults, the JSON config file,
        environment variables.

        Args:
            config_path: optional explicit Path to a JSON config file. If None,
                the loader will look for ``config.json`` in the home directory
                (``~/.rich-gradient`` unless ``RICH_GRADIENT_HOME_DIR`` is set).

        Environment variable overrides supported:
            RICH_GRADIENT_HOME_DIR -> directory containing ``config.json``
            RICH_GRADIENT_ANIMATE -> '1', 'true', 'yes', 'on' enable animation;
                '0', 'false', 'no', 'off' disable it
            RICH_GRADIENT_COLORS -> JSON object mapping name->color (merged)
            RICH_GRADIENT_EXE -> kept for external wrappers; unused by the core

        Invalid values (a malformed file, a non-boolean ``animate``, colors no
        parser understands) are ignored with a logged warning and the previous
        layer's value is kept.
        """

        merged: dict[str, Any] = json.loads(json.dumps(cls.DEFAULT_CONFIG))

        # The home directory decides where the config file lives, so the
        # environment override is applied before the file is read.
        home_env = os.environ.get("RICH_GRADIENT_HOME_DIR")
        if home_env:
            merged["rich-gradient-home-dir"] = home_env
        home_dir = Path(str(merged["rich-gradient-home-dir"])).expanduser()

        # step 1: read file if present
        cfg_file = (
            Path(config_path).expanduser()
            if config_path is not None
            else home_dir / "config.json"
        )
        file_colors: dict[str, str] = {}
        if cfg_file.exists():
            try:
                with cfg_file.open("r", encoding="utf8") as fh:
                    data = json.load(fh)
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning(f"Failed to load config file {cfg_file}: {exc}")
                data = None
            if isinstance(data, dict):
                if "colors" in data:
                    file_colors = _clean_colors(data.pop("colors"), source=str(cfg_file))
                if "animate" in data:
                    data["animate"] = _parse_bool(
                        data["animate"], default=merged["animate"], source=str(cfg_file)
                    )
                _deep_update(merged, data)
                logger.debug(f"Loaded rich-gradient config from {cfg_file}")
            elif data is not None:
                logger.warning(
                    f"Config file {cfg_file} did not contain a JSON object; ignoring"
                )

        # step 2: environment overrides
        exe_env = os.environ.get("RICH_GRADIENT_EXE")
        if exe_env:
            merged["exe"] = exe_env

        animate_env = os.environ.get("RICH_GRADIENT_ANIMATE")
        if animate_env is not None:
            merged["animate"] = _parse_bool(
                animate_env, default=merged["animate"], source="RICH_GRADIENT_ANIMATE"
            )

        env_colors: dict[str, str] = {}
        colors_env = os.environ.get("RICH_GRADIENT_COLORS")
        if colors_env:
            try:
                env_colors = _clean_colors(
                    json.loads(colors_env), source="RICH_GRADIENT_COLORS"
                )
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse RICH_GRADIENT_COLORS environment variable as JSON"
                )

        # Defaults first, then file, then environment, so missing keys fall back.
        colors = dict(cls.DEFAULT_CONFIG["colors"])
        colors.update(file_colors)
        colors.update(env_colors)

        return cls(
            animate=bool(merged["animate"]),
            colors=colors,
            home_dir=home_dir,
        )


config = RichGradientConfig.load()


def reload_config(config_path: Path | None = None) -> RichGradientConfig:
    """Reload the runtime configuration and return the new instance."""

    global config
    config = RichGradientConfig.load(config_path)
    return config
