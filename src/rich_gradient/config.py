"""Pure Python configuration backend used when pydantic-settings is unavailable."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional

from loguru import logger

from ._color_ext import install, is_installed

if not is_installed():
    install()


def _deep_update(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively update base dict with override and return base (mutates base)."""
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_update(base[k], v)
        else:
            base[k] = v
    return base


@dataclass
class Color:
    """Represents a color with a name and hex value."""

    name: str
    hex: str


@dataclass
class Colors:
    """Represents a collection of colors."""

    __root__: List[Color] = field(
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
            Color("hotpink", "#FF00AA"),
            Color("rose", "#FF0055"),
        ]
    )

    @property
    def names(self) -> List[str]:
        """Return a list of color names."""
        return [color.name for color in self.__root__]

    @property
    def hex(self) -> List[str]:
        """Return a list of color hex values."""
        return [color.hex for color in self.__root__]

    def as_dict(self) -> Dict[str, str]:
        """Return a dictionary mapping color names to hex values."""
        return {color.name: color.hex for color in self.__root__}

    @property
    def dict(self) -> Dict[str, str]:
        """Return a dictionary mapping color names to hex values."""
        return self.as_dict()


@dataclass(frozen=True)
class RichGradientConfig:
    """Pure-Python fallback configuration for rich-gradient.

    Use RichGradientConfig.load(...) to create an instance. The loader will:
    - start from DEFAULT_CONFIG
    - merge a JSON config file if present (by default: ~/.rich-gradient/config.json)
    - apply environment variable overrides

    Attributes (public API):
        exe: Path to the rich-gradient executable.
        animate: whether animations are enabled.
        colors: mapping of color-name -> hex value.
        path: Path to the config file that was loaded (or None).
        raw: merged raw configuration dict used to build this instance.
    """

    DEFAULT_CONFIG: ClassVar[dict] = {
        "rich-gradient-home-dir": str(Path.home() / ".rich-gradient"),
        "animate": True,
        "colors": Colors().as_dict(),
    }

    home_dir: Path
    animate: bool
    colors: Dict

    @property
    def spectrum_colors(self) -> List[str]:
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
    def load(cls, config_path: Optional[Path] = None) -> "RichGradientConfig":
        """Load configuration.

        Args:
            config_path: optional explicit Path to a JSON config file. If None,
                         the loader will look for $HOME/.rich-gradient/config.json.

        Environment variable overrides supported:
            RICH_GRADIENT_EXE -> string path to exe
            RICH_GRADIENT_ANIMATE -> '1','0','true','false' (case-insensitive)
            RICH_GRADIENT_COLORS -> JSON string of mapping name->hex (will merge)
            RICH_GRADIENT_HOME_DIR -> overrides rich-gradient-home-dir value
        """

        merged: Dict[str, Any] = json.loads(json.dumps(cls.DEFAULT_CONFIG))

        # step 1: read file if present
        # Allow environment to override home dir before attempting to read a
        # configuration file. This ensures callers can point the loader at a
        # temporary directory via RICH_GRADIENT_HOME_DIR and have the loader
        # pick up that config file on first import.
        home_env = os.environ.get("RICH_GRADIENT_HOME_DIR")
        if home_env:
            merged["rich-gradient-home-dir"] = home_env

        if config_path is None:
            home_dir = Path(
                merged.get("rich-gradient-home-dir", Path.home() / ".rich-gradient")
            )
            cfg_file = home_dir / "config.json"
        else:
            cfg_file = Path(config_path)

        if cfg_file.exists():
            try:
                with cfg_file.open("r", encoding="utf8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    _deep_update(merged, data)
                    logger.debug(f"Loaded rich-gradient config from {cfg_file}")
                else:
                    logger.warning(
                        f"Config file {cfg_file} did not contain a JSON object; ignoring"
                    )
            except (
                OSError,
                json.JSONDecodeError,
            ) as exc:  # pragma: no cover - defensive logging
                logger.exception(f"Failed to load config file {cfg_file}: {exc}")

        # step 2: environment overrides
        exe_env = os.environ.get("RICH_GRADIENT_EXE")
        if exe_env:
            merged["exe"] = exe_env

        animate_env = os.environ.get("RICH_GRADIENT_ANIMATE")
        if animate_env is not None:
            merged["animate"] = str(animate_env).lower() in ("1", "true", "yes", "on")

        home_env = os.environ.get("RICH_GRADIENT_HOME_DIR")
        if home_env:
            merged["rich-gradient-home-dir"] = home_env

        colors_env = os.environ.get("RICH_GRADIENT_COLORS")
        if colors_env:
            try:
                parsed = json.loads(colors_env)
                if isinstance(parsed, dict):
                    merged_colors = merged.setdefault("colors", {})
                    _deep_update(merged_colors, parsed)
                else:
                    logger.warning(
                        "RICH_GRADIENT_COLORS must be a JSON object mapping names to hex strings"
                    )
            except json.JSONDecodeError:
                logger.exception(
                    "Failed to parse RICH_GRADIENT_COLORS environment variable as JSON"
                )

        # ensure colors dict exists and merge with defaults so missing keys fall back
        merged_colors = dict(cls.DEFAULT_CONFIG.get("colors", {}))
        incoming_colors = merged.get("colors", {})
        _deep_update(merged_colors, incoming_colors)
        merged["colors"] = merged_colors

        # build final instance
        animate = bool(merged.get("animate", True))
        colors = dict(merged.get("colors", {}))

        home_dir_value = Path(
            str(
                merged.get(
                    "rich-gradient-home-dir",
                    cls.DEFAULT_CONFIG.get(
                        "rich-gradient-home-dir", Path.home() / ".rich-gradient"
                    ),
                )
            )
        )

        return cls(animate=animate, colors=colors, home_dir=home_dir_value)


config = RichGradientConfig.load()


def reload_config(config_path: Optional[Path] = None) -> RichGradientConfig:
    """Reload the runtime configuration and return the new instance."""

    global config  # noqa: PLW0603 - explicit module-level cache refresh
    config = RichGradientConfig.load(config_path)
    return config
