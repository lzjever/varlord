"""
Main Config class.

Provides high-level API for loading and managing configuration.
"""

from __future__ import annotations
from typing import Type, Any, List, Optional

from varlord.resolver import Resolver
from varlord.store import ConfigStore
from varlord.policy import PriorityPolicy
from varlord.sources.base import Source


class Config:
    """Main configuration manager.

    Provides a unified interface for loading configuration from multiple
    sources with customizable priority ordering.

    Example:
        >>> @dataclass
        ... class AppConfig:
        ...     host: str = "127.0.0.1"
        ...     port: int = 8000
        ...
        >>> cfg = Config(
        ...     model=AppConfig,
        ...     sources=[
        ...         sources.Defaults(model=AppConfig),
        ...         sources.Env(prefix="APP_"),
        ...         sources.CLI(),  # Model auto-injected
        ...     ],
        ... )
        >>> app = cfg.load()
        >>> print(app.host)
    """

    def __init__(
        self,
        model: Type[Any],
        sources: List[Source],
        policy: Optional[PriorityPolicy] = None,
        show_source_help: bool = True,
    ):
        """Initialize Config.

        Args:
            model: Dataclass model for configuration
            sources: List of configuration sources (order determines priority:
                    later sources override earlier ones)
            policy: Optional PriorityPolicy for per-key priority rules
            show_source_help: Whether to show source mapping help in errors (default: True)

        Raises:
            ModelDefinitionError: If any field is missing required/optional metadata

        Note:
            - Priority is determined by sources order: later sources override earlier ones
            - Use PriorityPolicy only when you need per-key priority rules
            - Model defaults are automatically applied as base layer (no need for Defaults source)
            - Model is automatically injected to all sources (no need to pass model to sources)
            - All fields MUST have explicit required/optional metadata
        """
        self._model = model
        self._sources = sources
        self._policy = policy
        self._show_source_help = show_source_help

        # Validate model definition first
        from varlord.model_validation import validate_model_definition

        validate_model_definition(model)

        # Auto-inject model to sources that need it
        self._inject_model_to_sources()

        # Note: Resolver will be created in load() with defaults source included

    def _inject_model_to_sources(self) -> None:
        """Automatically inject model to sources that need it."""
        for source in self._sources:
            if not hasattr(source, "_model") or source._model is None:
                source._model = self._model

    @classmethod
    def from_model(
        cls,
        model: Type[Any],
        cli: bool = True,
        dotenv: Optional[str] = ".env",
        etcd: Optional[dict] = None,
        policy: Optional[PriorityPolicy] = None,
    ) -> "Config":
        """Create Config with common sources (convenience method).

        Args:
            model: Dataclass model for configuration
            cli: Whether to include CLI source
            dotenv: Path to .env file (None to disable)
            etcd: Etcd configuration dict with keys: host, port, prefix, watch
            policy: Optional PriorityPolicy for per-key priority rules

        Returns:
            Config instance

        Note:
            - Model defaults are automatically applied as base layer
            - Source priority order: Defaults (auto) < DotEnv < Env < Etcd < CLI
            - All sources are filtered by model fields
            - All fields MUST have explicit required/optional metadata

        Example:
            >>> from dataclasses import dataclass, field
            >>> @dataclass
            ... class AppConfig:
            ...     host: str = field(default="127.0.0.1", )
            ...     port: int = field(default=8000, )
            >>> cfg = Config.from_model(
            ...     AppConfig,
            ...     cli=True,
            ...     dotenv=".env",
            ... )
        """
        from varlord import sources

        source_list: List[Source] = []

        # Env source (no prefix needed - filtered by model)
        source_list.append(sources.Env(model=model))

        if dotenv:
            try:
                source_list.append(sources.DotEnv(dotenv_path=dotenv, model=model))
            except ImportError:
                pass  # dotenv not installed

        if etcd:
            try:
                source_list.append(
                    sources.Etcd(
                        host=etcd.get("host", "127.0.0.1"),
                        port=etcd.get("port", 2379),
                        prefix=etcd.get("prefix", "/"),
                        watch=etcd.get("watch", False),
                        model=model,
                    )
                )
            except ImportError:
                pass  # etcd not installed

        if cli:
            source_list.append(sources.CLI(model=model))

        return cls(model=model, sources=source_list, policy=policy)

    def _extract_model_defaults(self) -> dict[str, Any]:
        """Extract default values from model (recursive, returns flat dict).

        Returns:
            Flat dictionary with normalized keys (e.g., {"host": "localhost", "db.host": "127.0.0.1"})
        """
        from varlord.metadata import get_all_fields_info

        defaults = {}
        field_infos = get_all_fields_info(self._model)

        for field_info in field_infos:
            normalized_key = field_info.normalized_key

            # Check for default value
            if field_info.default is not ...:
                defaults[normalized_key] = field_info.default
            # Check for default_factory
            elif field_info.default_factory is not ...:
                try:
                    defaults[normalized_key] = field_info.default_factory()
                except Exception:
                    pass  # Skip if factory fails

        return defaults

    def _create_defaults_source(self) -> Source:
        """Create an internal Defaults source from model defaults.

        Returns:
            A Source instance that returns model defaults.
        """
        from varlord.sources.defaults import Defaults

        # Create Defaults source with precomputed defaults
        defaults_source = Defaults(model=self._model)
        # Precompute defaults to avoid repeated extraction
        defaults_source._precomputed_defaults = self._extract_model_defaults()
        return defaults_source

    def _load_config_dict(self, validate: bool = False) -> dict[str, Any]:
        """Load and merge configuration from all sources.

        Args:
            validate: Whether to validate required fields

        Returns:
            Merged configuration dictionary

        Raises:
            RequiredFieldError: If required fields are missing and validate=True
        """
        # Step 1: Create defaults source (internal, not in user's sources list)
        defaults_source = self._create_defaults_source()

        # Step 2: Combine defaults + user sources
        all_sources = [defaults_source] + self._sources

        # Step 3: Create resolver with all sources
        resolver = Resolver(sources=all_sources, policy=self._policy)

        # Step 4: Resolve (merge all sources)
        config_dict = resolver.resolve()

        # Step 5: Validate (if enabled)
        if validate:
            self.validate(config_dict)

        return config_dict

    def validate(self, config_dict: Optional[dict[str, Any]] = None) -> None:
        """Validate configuration.

        Args:
            config_dict: Optional configuration dict to validate.
                        If None, loads and validates current configuration.

        Raises:
            RequiredFieldError: If required fields are missing.
        """
        if config_dict is None:
            # Load configuration first (without validation)
            config_dict = self._load_config_dict(validate=False)

        # Validate
        from varlord.model_validation import validate_config

        validate_config(self._model, config_dict, self._sources, self._show_source_help)

    def handle_cli_commands(self) -> None:
        """Handle CLI commands (--help/-h and --check-variables/-cv) using current config.

        This method processes basic CLI commands based on the current configuration.
        It should be called once at program startup, before calling load().
        It handles CLI commands and exits if necessary:
        - --help/-h: Shows help with source priority and mapping rules, then exits with code 0
        - --check-variables/-cv: Shows diagnostic table and exits with code 1 if required fields are missing

        Note:
            This method uses the current Config's sources and model to generate help information.
            It is designed to be called once at startup. After this method returns
            (without exiting), you can safely call load() to get the configuration.
        """
        help_shown, cv_shown = self.handle_cli_flags(
            exit_on_help=True, exit_on_check_variables=False
        )

        # If check-variables was shown, check if there are missing required fields
        # and exit early to avoid showing validation error after diagnostic table
        if cv_shown:
            config_dict_preview = self._load_config_dict(validate=False)
            from varlord.metadata import get_all_fields_info

            # Check for missing required fields
            missing_fields = []
            for field_info in get_all_fields_info(self._model):
                if field_info.required:
                    key = field_info.normalized_key
                    if key not in config_dict_preview or config_dict_preview.get(key) is None:
                        missing_fields.append(key)

            if missing_fields:
                # Print a message before exiting
                import sys
                import os

                print("")
                print(f"⚠️  Missing required fields: {', '.join(missing_fields)}")
                print("   Exiting with code 1. Please provide these fields and try again.")
                prog_name = os.path.basename(sys.argv[0]) if sys.argv else "app.py"
                print(f"   For help, run: python {prog_name} --help")
                sys.exit(1)

    def load(self, validate: bool = True) -> Any:
        """Load configuration with automatic defaults and optional validation.

        Args:
            validate: Whether to validate required fields (default: True)

        Returns:
            Model instance with configuration loaded from all sources.

        Raises:
            RequiredFieldError: If required fields are missing and validate=True.

        Note:
            This method loads configuration once. For dynamic updates,
            use load_store() instead.

            For handling CLI commands (--help, --check-variables), call handle_cli_commands() first.
        """
        # Load and merge configuration
        config_dict = self._load_config_dict(validate=validate)

        # Convert to model instance
        return self._dict_to_model(config_dict)

    def load_store(self) -> ConfigStore:
        """Load configuration store (supports dynamic updates).

        Automatically enables watch if any source supports it.

        Returns:
            ConfigStore instance for runtime configuration management.

        Note:
            ConfigStore will use the same defaults + sources logic.
        """
        # Create defaults source
        defaults_source = self._create_defaults_source()

        # Combine all sources
        all_sources = [defaults_source] + self._sources

        # Create resolver
        resolver = Resolver(sources=all_sources, policy=self._policy)

        # Create and return ConfigStore
        return ConfigStore(resolver=resolver, model=self._model)

    def _dict_to_model(self, config_dict: dict[str, Any]) -> Any:
        """Convert dictionary to model instance.

        Supports both flat keys (host) and nested keys (db.host) with automatic
        mapping to nested dataclass structures.

        Args:
            config_dict: Configuration dictionary with keys in dot notation (e.g., "db.host")

        Returns:
            Model instance
        """
        from dataclasses import is_dataclass

        if not is_dataclass(self._model):
            raise TypeError(f"Model must be a dataclass, got {type(self._model)}")

        # Convert flat dict with dot notation to nested structure
        nested_dict = self._flatten_to_nested(config_dict, self._model)

        # Log successful load
        try:
            from varlord.logging import log_config_loaded

            log_config_loaded(self._model.__name__, list(nested_dict.keys()))
        except ImportError:
            pass

        # Create model instance
        # Validation should be done in model's __post_init__ method
        return self._model(**nested_dict)

    def _flatten_to_nested(self, flat_dict: dict[str, Any], model: type) -> dict[str, Any]:
        """Convert flat dict with dot notation to nested structure.

        Example:
            {"db.host": "localhost", "db.port": 5432, "host": "0.0.0.0"}
            → {"db": {"host": "localhost", "port": 5432}, "host": "0.0.0.0"}

        Args:
            flat_dict: Flat dictionary with dot-notation keys
            model: Dataclass model to map to

        Returns:
            Nested dictionary matching the model structure
        """
        from dataclasses import fields, is_dataclass, asdict
        from varlord.converters import convert_value

        field_info = {f.name: f for f in fields(model)}
        result: dict[str, Any] = {}

        # Step 1: Convert all dataclass instances in flat_dict to dicts
        flat_dict_processed = {}
        for key, value in flat_dict.items():
            if is_dataclass(type(value)):
                flat_dict_processed[key] = asdict(value)
            else:
                flat_dict_processed[key] = value

        # Step 2: Process flat keys first (non-nested)
        for key, value in flat_dict_processed.items():
            if "." not in key:
                if key in field_info:
                    field = field_info[key]
                    try:
                        converted_value = convert_value(value, field.type, key=key)
                        result[key] = converted_value
                    except (ValueError, TypeError):
                        result[key] = value

        # Step 3: Process nested keys
        for key, value in flat_dict_processed.items():
            if "." in key:
                parts = key.split(".", 1)
                parent_key = parts[0]
                child_key = parts[1]

                if parent_key in field_info:
                    field = field_info[parent_key]
                    if is_dataclass(field.type):
                        # Initialize parent dict if needed
                        if parent_key not in result:
                            # Use value from flat_dict_processed if available
                            if parent_key in flat_dict_processed:
                                parent_value = flat_dict_processed[parent_key]
                                if isinstance(parent_value, dict):
                                    result[parent_key] = parent_value.copy()
                                else:
                                    result[parent_key] = {}
                            else:
                                result[parent_key] = {}
                        elif not isinstance(result[parent_key], dict):
                            result[parent_key] = {}

                        # Recursively process nested structure
                        # First, get existing nested values to preserve them
                        existing_nested = {}
                        if parent_key in result and isinstance(result[parent_key], dict):
                            for k, v in result[parent_key].items():
                                if is_dataclass(type(v)):
                                    existing_nested[k] = asdict(v)
                                elif isinstance(v, dict):
                                    existing_nested[k] = v.copy()
                                else:
                                    existing_nested[k] = v

                        # Merge existing values with the new nested key
                        nested_flat = {child_key: value}
                        if existing_nested:
                            # Merge existing nested values into nested_flat for recursive processing
                            for k, v in existing_nested.items():
                                if k not in nested_flat:
                                    nested_flat[k] = v

                        nested_result = self._flatten_to_nested(nested_flat, field.type)

                        # Update result[parent_key] with nested_result (all values are now in nested_result)
                        for nested_key, nested_value in nested_result.items():
                            if is_dataclass(type(nested_value)):
                                result[parent_key][nested_key] = asdict(nested_value)
                            else:
                                result[parent_key][nested_key] = nested_value

        # Step 4: Convert nested dicts to dataclass instances with type conversion
        for key, value in list(result.items()):
            if key in field_info:
                field = field_info[key]
                if is_dataclass(field.type) and isinstance(value, dict):
                    # First, convert any dataclass instances in value to dicts
                    value_dict = {}
                    for nested_key, nested_value in value.items():
                        if is_dataclass(type(nested_value)):
                            value_dict[nested_key] = asdict(nested_value)
                        else:
                            value_dict[nested_key] = nested_value
                    # Recursively process and convert types
                    nested_instance = self._flatten_to_nested(value_dict, field.type)
                    # Convert all values to correct types
                    nested_fields = {f.name: f for f in fields(field.type)}
                    for nested_key, nested_value in nested_instance.items():
                        if nested_key in nested_fields:
                            nested_field = nested_fields[nested_key]
                            try:
                                nested_instance[nested_key] = convert_value(
                                    nested_value, nested_field.type, key=f"{key}.{nested_key}"
                                )
                            except (ValueError, TypeError):
                                pass
                    result[key] = field.type(**nested_instance)

        return result

    def format_cli_help(self, prog: Optional[str] = None) -> str:
        """Generate CLI help text from model fields with source priority and mapping rules.

        This method finds the CLI source and generates help text without
        using argparse's built-in help, giving varlord complete control.
        It also includes source priority information and mapping rules.

        Args:
            prog: Program name (default: script name from sys.argv[0])

        Returns:
            Formatted help text string, or empty string if no CLI source found
        """
        from varlord.sources.cli import CLI

        # Find CLI source
        cli_source = None
        for source in self._sources:
            if isinstance(source, CLI):
                cli_source = source
                break

        if not cli_source:
            return ""

        # Get basic help from CLI source
        help_text = cli_source.format_help(prog=prog)

        # Add standard command-line options at the beginning
        help_text = self._format_standard_options(prog=prog) + help_text

        # Add mapping rules (source priority moved to check-variables)
        help_text += self._format_source_mapping_rules(prog=prog)

        return help_text

    def _format_standard_options(self, prog: Optional[str] = None) -> str:
        """Format standard command-line options that all varlord apps support.

        Args:
            prog: Program name for examples (default: script name from sys.argv[0])

        Returns:
            Formatted string with standard options
        """
        import os
        import sys

        if prog is None:
            prog = os.path.basename(sys.argv[0]) if sys.argv else "app.py"

        lines = []
        lines.append("Standard Options:")
        lines.append("")
        lines.append("  --help, -h")
        lines.append("    Show this help message and exit")
        lines.append("")
        lines.append("  --check-variables, -cv")
        lines.append("    Show diagnostic table of all configuration variables and exit")
        lines.append(
            "    Displays variable status (Required/Optional, Loaded/Missing, Source, Value)"
        )
        lines.append("")
        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def _format_source_priority_info(self) -> str:
        """Format source priority information for help output.

        Returns:
            Formatted string showing source priority order
        """
        lines = []
        lines.append("")
        lines.append("Configuration Source Priority:")
        lines.append("  (Later sources override earlier ones)")
        lines.append("")

        # Include defaults (always first)
        lines.append("  1. Model Defaults (lowest priority)")

        # Add user sources
        for i, source in enumerate(self._sources, start=2):
            source_name = source.name
            # Make source name more readable
            if source_name == "env":
                source_name = "Environment Variables"
            elif source_name == "cli":
                source_name = "Command Line Arguments"
            elif source_name == "dotenv":
                source_name = ".env File"
            elif source_name == "etcd":
                source_name = "Etcd"
            else:
                source_name = source_name.capitalize()

            lines.append(f"  {i}. {source_name}")

        lines.append("")
        return "\n".join(lines)

    def _format_source_mapping_rules(self, prog: Optional[str] = None) -> str:
        """Format source mapping rules for help output.

        Args:
            prog: Program name for CLI examples (not used, kept for compatibility)

        Returns:
            Formatted string with link to mapping rules documentation
        """
        lines = []
        lines.append("Variable Mapping Rules:")
        lines.append("")
        lines.append("  For detailed mapping rules and examples for each source type, see:")
        lines.append("  https://varlord.readthedocs.io/en/latest/user_guide/key_mapping.html")
        lines.append("")

        return "\n".join(lines)

    def format_diagnostic_table(self) -> str:
        """Generate diagnostic table showing all variables and their status.

        Returns:
            Formatted ASCII table string showing:
            - Variable name
            - Required/Optional status
            - Load status (Loaded/Using Default/Missing)
            - Source (defaults/env/cli/dotenv/etc)
            - Value (if loaded)
        """
        from varlord.metadata import get_all_fields_info

        # Get all field info
        field_infos = get_all_fields_info(self._model)

        # Load configuration from all sources (without validation)
        config_dict = self._load_config_dict(validate=False)

        # Load each source individually to determine source for each key
        defaults_source = self._create_defaults_source()
        all_sources = [defaults_source] + self._sources

        # Load from each source
        source_configs: dict[str, dict[str, Any]] = {}
        for source in all_sources:
            try:
                source_configs[source.name] = dict(source.load())
            except Exception:
                source_configs[source.name] = {}

        # Build table rows
        rows = []
        for field_info in field_infos:
            key = field_info.normalized_key
            value = config_dict.get(key)

            # Determine status
            if value is None or (isinstance(value, str) and value == ""):
                # Check if it's actually missing or just empty
                if key not in config_dict:
                    status = "Missing"
                else:
                    status = "Loaded (empty)"
            else:
                status = "Loaded"

            # Determine source
            source_name = "defaults"
            for source in reversed(all_sources):  # Check in reverse order (highest priority first)
                if key in source_configs.get(source.name, {}):
                    source_name = source.name
                    break

            # Check if using default
            if source_name == "defaults" and field_info.default is not ...:
                status = "Using Default"
            elif source_name == "defaults" and field_info.default_factory is not ...:
                status = "Using Default (factory)"

            # Format value for display
            if value is None:
                value_str = "None"
            elif isinstance(value, str) and len(value) > 40:
                value_str = value[:37] + "..."
            else:
                value_str = str(value)

            # Required/Optional
            req_status = "Required" if field_info.required else "Optional"

            rows.append(
                {
                    "variable": key,
                    "required": req_status,
                    "status": status,
                    "source": source_name,
                    "value": value_str,
                }
            )

        # Generate variable diagnostic table
        variable_table = self._format_ascii_table(rows)

        # Generate source information table
        source_table = self._format_source_info_table(all_sources)

        # Combine both tables
        return variable_table + "\n" + source_table

    def _format_ascii_table(self, rows: List[dict[str, str]]) -> str:
        """Format rows as an ASCII table using prettytable.

        Args:
            rows: List of dictionaries with keys: variable, required, status, source, value

        Returns:
            Formatted ASCII table string
        """
        try:
            from prettytable import PrettyTable
        except ImportError:
            # Fallback to simple format if prettytable is not available
            if not rows:
                return "No variables defined in model.\n"
            lines = []
            lines.append("Configuration Variables Status:")
            lines.append("")
            for row in rows:
                lines.append(
                    f"  {row['variable']} ({row['required']}) - {row['status']} - {row['source']} - {row['value']}"
                )
            return "\n".join(lines) + "\n"

        if not rows:
            return "No variables defined in model.\n"

        # Create table
        table = PrettyTable()
        table.field_names = ["Variable", "Required", "Status", "Source", "Value"]

        # Add rows
        for row in rows:
            table.add_row(
                [
                    row["variable"],
                    row["required"],
                    row["status"],
                    row["source"],
                    row["value"],
                ]
            )

        # Set table style (compact, left-aligned for better readability)
        table.align = "l"
        table.padding_width = 1

        return table.get_string() + "\n"

    def _format_source_info_table(self, all_sources: List[Source]) -> str:
        """Format detailed source information table.

        Args:
            all_sources: List of all sources (including defaults)

        Returns:
            Formatted ASCII table string with source details
        """
        try:
            from prettytable import PrettyTable
        except ImportError:
            # Fallback if prettytable is not available
            lines = []
            lines.append("Configuration Source Priority and Details:")
            lines.append("")
            lines.append("  1. Model Defaults (lowest priority)")
            for i, source in enumerate(all_sources[1:], start=2):
                source_name = self._get_readable_source_name(source.name)
                lines.append(f"  {i}. {source_name}")
            lines.append("")
            return "\n".join(lines)

        table = PrettyTable()
        table.field_names = [
            "Priority",
            "Source Name",
            "Parameters",
            "Load Time (ms)",
            "Watch Support",
            "Last Update",
        ]
        table.align = "l"
        table.padding_width = 1

        # Include defaults (always first)
        defaults_source = all_sources[0] if all_sources else None
        if defaults_source:
            load_time = self._measure_source_load_time(defaults_source)
            table.add_row(
                [
                    "1 (lowest)",
                    "Model Defaults",
                    "N/A",
                    f"{load_time:.2f}",
                    "No",
                    "N/A",
                ]
            )

        # Add user sources
        for i, source in enumerate(all_sources[1:], start=2):
            source_name = self._get_readable_source_name(source.name)
            params = self._get_source_parameters(source)
            load_time = self._measure_source_load_time(source)
            watch_support = "Yes" if source.supports_watch() else "No"
            last_update = "N/A"  # TODO: Track last update time if needed

            table.add_row(
                [
                    str(i),
                    source_name,
                    params,
                    f"{load_time:.2f}",
                    watch_support,
                    last_update,
                ]
            )

        lines = []
        lines.append("Configuration Source Priority and Details:")
        lines.append("")
        lines.append(table.get_string())
        lines.append("")
        lines.append("Note: Later sources override earlier ones (higher priority).")
        lines.append("")

        return "\n".join(lines)

    def _get_readable_source_name(self, source_name: str) -> str:
        """Get readable name for a source.

        Args:
            source_name: Source name

        Returns:
            Readable source name
        """
        name_map = {
            "env": "Environment Variables",
            "cli": "Command Line Arguments",
            "dotenv": ".env File",
            "etcd": "Etcd",
            "defaults": "Model Defaults",
        }
        return name_map.get(source_name, source_name.capitalize())

    def _get_source_parameters(self, source: Source) -> str:
        """Get source parameters as a string.

        Args:
            source: Source instance

        Returns:
            Parameters string
        """
        try:
            # Try to get parameters from source attributes
            params = []
            source_type = type(source).__name__

            if source_type == "Env":
                # Env has no prefix anymore, just model
                params.append("model-based")
            elif source_type == "CLI":
                # CLI has model and optional argv
                params.append("model-based")
            elif source_type == "DotEnv":
                # DotEnv has path
                if hasattr(source, "_dotenv_path"):
                    params.append(f"path={source._dotenv_path}")
                if hasattr(source, "_model") and source._model:
                    params.append("model-based")
            elif source_type == "Etcd":
                # Etcd has host, port, prefix, watch
                if hasattr(source, "_host"):
                    params.append(f"host={source._host}")
                if hasattr(source, "_port"):
                    params.append(f"port={source._port}")
                if hasattr(source, "_prefix"):
                    params.append(f"prefix={source._prefix}")
                if hasattr(source, "_watch"):
                    params.append(f"watch={source._watch}")
            elif source_type == "_DefaultsSource":
                params.append("from model")

            return ", ".join(params) if params else "N/A"
        except Exception:
            return "N/A"

    def _measure_source_load_time(self, source: Source) -> float:
        """Measure source load time in milliseconds.

        Args:
            source: Source instance

        Returns:
            Load time in milliseconds
        """
        import time

        try:
            start = time.perf_counter()
            source.load()
            end = time.perf_counter()
            return (end - start) * 1000  # Convert to milliseconds
        except Exception:
            return 0.0

    def handle_cli_flags(
        self,
        exit_on_help: bool = True,
        exit_on_check_variables: bool = False,
        prog: Optional[str] = None,
    ) -> tuple[bool, bool]:
        """Handle CLI flags (--help/-h and --check-variables/-cv).

        Args:
            exit_on_help: If True, exit after showing help (default: True)
            exit_on_check_variables: If True, exit after showing diagnostic table (default: False)
            prog: Program name for help text (default: script name from sys.argv[0])

        Returns:
            Tuple of (help_shown, check_variables_shown)

        Note:
            This method checks sys.argv for --help/-h and --check-variables/-cv flags.
            If help is shown and exit_on_help=True, the program will exit.
            If check_variables is shown and exit_on_check_variables=True, the program will exit.
        """
        import sys

        help_shown = False
        check_variables_shown = False

        # Check for --help or -h
        if "--help" in sys.argv or "-h" in sys.argv:
            help_text = self.format_cli_help(prog=prog)
            if help_text:
                print(help_text)
                help_shown = True
                if exit_on_help:
                    sys.exit(0)

        # Check for --check-variables or -cv
        if "--check-variables" in sys.argv or "-cv" in sys.argv:
            diagnostic_table = self.format_diagnostic_table()
            print(diagnostic_table)
            check_variables_shown = True
            if exit_on_check_variables:
                sys.exit(0)

        return (help_shown, check_variables_shown)

    def get_field_info(self) -> List[Any]:
        """Get information about all fields in the model.

        Returns:
            List of FieldInfo objects for all fields (including nested)
        """
        from varlord.metadata import get_all_fields_info

        return get_all_fields_info(self._model)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Config(model={self._model.__name__}, sources={len(self._sources)})>"
