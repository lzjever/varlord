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
            - Model is automatically injected to all sources
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
            ...     host: str = field(default="127.0.0.1", metadata={"optional": True})
            ...     port: int = field(default=8000, metadata={"optional": True})
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

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Config(model={self._model.__name__}, sources={len(self._sources)})>"
