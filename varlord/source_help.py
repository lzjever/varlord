"""
Source mapping help and examples.

Provides functions to generate source mapping examples and format error messages
with actionable guidance.
"""

from __future__ import annotations

from typing import Any, List, Type

from varlord.metadata import get_field_info
from varlord.sources.base import Source


def generate_env_example(field_key: str, field_type: Type[Any]) -> str:
    """Generate example for Env source.

    Args:
        field_key: Normalized field key (e.g., "api_key" or "db.host")
        field_type: Field type

    Returns:
        Example string showing how to set environment variable
    """
    # Convert to uppercase with underscores
    env_key = field_key.upper().replace(".", "__")
    example_value = _get_example_value(field_type)
    return f"export {env_key}={example_value!r}"


def generate_cli_example(field_key: str, field_type: Type[Any]) -> str:
    """Generate example for CLI source.

    Args:
        field_key: Normalized field key (e.g., "api_key" or "db.host")
        field_type: Field type

    Returns:
        Example string showing how to use CLI argument
    """
    # Convert to CLI argument format
    arg_name = field_key.replace(".", "-").replace("_", "-")
    example_value = _get_example_value(field_type)

    if field_type is bool:
        return f"--{arg_name}"
    else:
        return f"--{arg_name} {example_value!r}"


def generate_dotenv_example(field_key: str, field_type: Type[Any]) -> str:
    """Generate example for DotEnv source.

    Args:
        field_key: Normalized field key (e.g., "api_key" or "db.host")
        field_type: Field type

    Returns:
        Example string showing how to set .env variable
    """
    # Convert to uppercase with double underscores for nesting
    env_key = field_key.upper().replace(".", "__")
    example_value = _get_example_value(field_type)
    return f"{env_key}={example_value}"


def _get_example_value(field_type: Type[Any]) -> str:
    """Get example value for a field type.

    Args:
        field_type: Field type

    Returns:
        Example value string
    """
    if field_type is bool:
        return "true"
    elif field_type is int:
        return "123"
    elif field_type is float:
        return "3.14"
    else:
        return "value"


def format_source_help(sources: List[Source], missing_fields: List[str]) -> str:
    """Format source mapping help for missing fields.

    Args:
        sources: List of sources configured
        missing_fields: List of normalized keys of missing required fields

    Returns:
        Formatted help text with examples for each source
    """
    if not missing_fields or not sources:
        return ""

    lines = []
    lines.append("To provide these parameters, use one of the following methods:")
    lines.append("")

    # Group sources by type
    source_types = {}
    for source in sources:
        source_type = source.name
        if source_type not in source_types:
            source_types[source_type] = []
        source_types[source_type].append(source)

    # Generate examples for each source type (without ASCII boxes)
    if "env" in source_types:
        lines.append("Environment Variables:")
        for field_key in missing_fields:
            # Try to get field type from first source's model
            field_type = str  # Default
            if sources and hasattr(sources[0], "_model") and sources[0]._model:
                field_info = get_field_info(sources[0]._model, field_key)
                if field_info:
                    field_type = field_info.type

            example = generate_env_example(field_key, field_type)
            lines.append(f"  {example}")
        lines.append("  Note: Use double underscore (__) for nested keys")
        lines.append("")

    if "cli" in source_types:
        lines.append("Command Line Arguments:")
        for field_key in missing_fields:
            # Try to get field type from first source's model
            field_type = str  # Default
            if sources and hasattr(sources[0], "_model") and sources[0]._model:
                field_info = get_field_info(sources[0]._model, field_key)
                if field_info:
                    field_type = field_info.type

            example = generate_cli_example(field_key, field_type)
            lines.append(f"  python app.py {example}")
        lines.append("  Note: Use hyphens or underscores (both work)")
        lines.append("")

    if "dotenv" in source_types:
        lines.append(".env File:")
        lines.append("  Create .env file with:")
        for field_key in missing_fields:
            # Try to get field type from first source's model
            field_type = str  # Default
            if sources and hasattr(sources[0], "_model") and sources[0]._model:
                field_info = get_field_info(sources[0]._model, field_key)
                if field_info:
                    field_type = field_info.type

            example = generate_dotenv_example(field_key, field_type)
            lines.append(f"  {example}")
        lines.append("  Note: Use double underscore (__) for nested keys")
        lines.append("")

    lines.append("For detailed mapping rules, see:")
    lines.append("  https://varlord.readthedocs.io/en/latest/user_guide/key_mapping.html")
    lines.append("")
    lines.append("For more information, run: python app.py --help")

    return "\n".join(lines)
