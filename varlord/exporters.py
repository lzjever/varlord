"""
Configuration export utilities.

Provides functions to export configuration to various file formats:
JSON, YAML, TOML, and .env files.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Union


def to_dict(config: Any) -> dict[str, Any]:
    """Convert configuration object to dictionary.

    Handles nested dataclasses by converting them recursively.

    Args:
        config: Configuration object (dataclass instance)

    Returns:
        Dictionary representation of the configuration
    """
    if is_dataclass(config):
        return asdict(config)
    elif isinstance(config, dict):
        return config
    else:
        raise TypeError(f"Cannot convert {type(config)} to dictionary")


def export_json(config: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """Export configuration to JSON file.

    Args:
        config: Configuration object or dictionary
        file_path: Path to output JSON file
        indent: JSON indentation (default: 2)

    Example:
        >>> cfg = Config(model=AppConfig, sources=[...])
        >>> app = cfg.load()
        >>> export_json(app, "config.json")
    """
    import json

    config_dict = to_dict(config)
    file_path = Path(file_path)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(config_dict, f, indent=indent, ensure_ascii=False)


def export_yaml(config: Any, file_path: Union[str, Path], default_flow_style: bool = False) -> None:
    """Export configuration to YAML file.

    Args:
        config: Configuration object or dictionary
        file_path: Path to output YAML file
        default_flow_style: Use flow style (default: False, uses block style)

    Example:
        >>> cfg = Config(model=AppConfig, sources=[...])
        >>> app = cfg.load()
        >>> export_yaml(app, "config.yaml")

    Raises:
        ImportError: If PyYAML is not installed
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for YAML export. Install it with: pip install pyyaml")

    config_dict = to_dict(config)
    file_path = Path(file_path)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(
            config_dict,
            f,
            default_flow_style=default_flow_style,
            allow_unicode=True,
            sort_keys=False,
        )


def export_toml(config: Any, file_path: Union[str, Path]) -> None:
    """Export configuration to TOML file.

    Args:
        config: Configuration object or dictionary
        file_path: Path to output TOML file

    Example:
        >>> cfg = Config(model=AppConfig, sources=[...])
        >>> app = cfg.load()
        >>> export_toml(app, "config.toml")

    Raises:
        ImportError: If tomli-w is not available
    """
    try:
        import tomli_w
    except ImportError:
        raise ImportError(
            "tomli-w is required for TOML export. Install it with: pip install tomli-w"
        )

    config_dict = to_dict(config)
    file_path = Path(file_path)

    with open(file_path, "wb") as f:
        tomli_w.dump(config_dict, f)


def export_env(
    config: Any,
    file_path: Union[str, Path],
    prefix: str = "",
    uppercase: bool = True,
    nested_separator: str = "__",
) -> None:
    """Export configuration to .env file.

    Args:
        config: Configuration object or dictionary
        file_path: Path to output .env file
        prefix: Optional prefix for all environment variable names (e.g., "APP_")
        uppercase: Convert keys to uppercase (default: True)
        nested_separator: Separator for nested keys (default: "__")

    Example:
        >>> cfg = Config(model=AppConfig, sources=[...])
        >>> app = cfg.load()
        >>> export_env(app, ".env", prefix="APP_")
        # Creates: APP_HOST=localhost
        #          APP_PORT=8000
    """
    config_dict = to_dict(config)
    file_path = Path(file_path)

    def flatten_dict(d: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
        """Flatten nested dictionary."""
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    # Flatten nested structure
    flat_dict = flatten_dict(config_dict, sep=nested_separator)

    with open(file_path, "w", encoding="utf-8") as f:
        for key, value in sorted(flat_dict.items()):
            # Format key
            env_key = key.replace(".", nested_separator)
            if uppercase:
                env_key = env_key.upper()
            env_key = f"{prefix}{env_key}"

            # Format value
            if value is None:
                env_value = ""
            elif isinstance(value, bool):
                env_value = "true" if value else "false"
            elif isinstance(value, (list, tuple)):
                # Convert list to comma-separated string
                env_value = ",".join(str(item) for item in value)
            else:
                env_value = str(value)

            # Write line
            # Escape special characters in value
            if " " in env_value or "#" in env_value or "=" in env_value:
                env_value = f'"{env_value}"'
            f.write(f"{env_key}={env_value}\n")
