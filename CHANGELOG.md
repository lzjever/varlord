# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-01-08

### Added
- **Env Source Prefix Support**: Added `prefix` parameter to `Env` source for filtering environment variables
  - `sources.Env(prefix="TITAN__")` - Only loads environment variables starting with the specified prefix
  - Case-insensitive prefix matching (e.g., `titan__` matches `TITAN__`)
  - Prefix is automatically removed before key normalization
  - Useful for isolating application-specific environment variables in containerized deployments
- **Enhanced Nested Dataclass Validation**: Improved validation logic for nested dataclass fields
  - Parent dataclass fields are now considered "present" if any of their child fields exist
  - Fixes false positive `RequiredFieldError` when nested fields are provided via dot notation
- **Improved `_flatten_to_nested` Method**: Enhanced nested dataclass instantiation from flattened dictionaries
  - Now correctly collects all child keys for a parent before recursively processing them
  - Properly handles `Optional[Dataclass]` types
  - Filters out `init=False` fields before passing arguments to dataclass constructors
  - Fixes `TypeError` when instantiating nested dataclasses with multiple required fields

### Fixed
- Fixed `_flatten_to_nested` bug where only partial fields were passed to nested dataclass constructors
- Fixed validation logic incorrectly flagging parent dataclass fields as missing when child fields were present
- Fixed handling of `init=False` fields in nested dataclass instantiation
- Fixed `Optional[Dataclass]` type handling in nested configuration loading

### Changed
- `Env` source now supports optional `prefix` parameter (backward compatible)
- Enhanced error messages for nested configuration validation

## [0.6.0] - 2026-01-08

### Added
- **File-Based Sources**: New YAML, JSON, and TOML sources for loading configuration from files
  - `sources.YAML(file_path, ...)` - Load configuration from YAML files
  - `sources.JSON(file_path, ...)` - Load configuration from JSON files
  - `sources.TOML(file_path, ...)` - Load configuration from TOML files
  - All file sources support nested configuration structures (automatically flattened to dot notation)
  - All file sources support `required=False` parameter for graceful handling of missing files
  - Missing files return empty dict and show "Not Available" status in `--check-variables`
- **Source ID System**: Enhanced source identification for multiple sources of the same type
  - Each source now has a unique `id` property (in addition to `name`)
  - Custom source IDs can be specified via `source_id` parameter
  - Automatic ID generation based on source type and key parameters
  - `PriorityPolicy` now supports both source names and source IDs
  - Multiple sources of the same type can be used with different priorities
- **Enhanced Diagnostic Table**: Improved `--check-variables` output
  - Added "Status" column showing source load status ("Active", "Not Available", "Failed: ...")
  - Better error messages for missing files (shows "Not Available" instead of "Error")
  - Source status tracking via `load_status` and `load_error` properties
- **Improved Error Messages**: Required field errors now include field descriptions from metadata
  - `RequiredFieldError` messages now show field descriptions when available
  - More user-friendly error messages with actionable guidance

### Changed
- **Dependencies**: Moved `python-dotenv`, `pyyaml`, and `tomli` from optional to core dependencies
  - `dotenv`, `yaml`, and `toml` sources are now always available
  - Only `etcd` remains as an optional dependency
- **Etcd Source**: Removed `Etcd.from_env()` method
  - All parameters must now be passed explicitly via `__init__`
  - Users should read environment variables themselves and pass to `Etcd()`
  - This aligns with the principle that the library should not implicitly read environment variables for its own configuration
- **Source Base Class**: Enhanced `Source` base class with status tracking
  - Added `_load_status` attribute ("success", "not_found", "failed", "unknown")
  - Added `_load_error` attribute for error messages
  - Added `load_status` and `load_error` properties
  - Modified `load()` to wrap `_do_load()` with proper error handling
  - Subclasses should implement `_do_load()` instead of `load()`
- **Key Mapping**: File-based sources (YAML, JSON, TOML) use recursive flattening
  - Nested dictionaries are automatically flattened to dot notation (e.g., `{"db": {"host": "localhost"}}` → `{"db.host": "localhost"}`)
  - Consistent with existing key mapping rules (`__` → `.`, `_` preserved, lowercase)
- **Examples**: Updated all examples to use best practices
  - Use nested dataclasses instead of double-underscore fields
  - Include field descriptions in metadata
  - Proper error handling with `RequiredFieldError`
  - Support for `--help` and `-cv` flags

### Fixed
- Fixed "Unknown" status in diagnostic table for Env, CLI, Defaults, and DotEnv sources
- Fixed source status tracking to correctly show "Active", "Not Available", or "Failed" status
- Improved test coverage for file-based sources and multiple sources of the same type

## [0.5.0] - 2026-01-07

### Fixed
- Fixed Sphinx documentation build error where "etcd" was being interpreted as an unknown reference target
- Added dummy reference target for "etcd" in Sphinx configuration to resolve docutils errors
- Escaped "etcd" and "Etcd" references in docstrings to prevent false positive cross-reference errors

### Changed
- Improved documentation build reliability by properly handling reference targets in docstrings

## [0.4.0] - 2026-01-03

### Changed
- Updated Python version support to 3.8-3.14
- Integrated CI workflow with uv for automated testing and building

## [0.3.0] - 2026-01-03

### Added
- **Etcd Source Enhancements**: 
  - TLS/SSL certificate support for secure connections
  - User authentication support
  - `from_env()` method for configuration from environment variables
  - Comprehensive watch support for dynamic configuration updates
  - Full integration with ConfigStore and subscribe mechanism
- **UV Dependency Management**: 
  - Migrated from conda to uv for faster dependency management
  - Added `setup-venv` command for CI/CD workflows (dependencies only)
  - Automatic uv detection with fallback to pip
- **Documentation**:
  - Complete etcd source documentation in Sphinx
  - Comprehensive watch and dynamic updates examples
  - Contributing guidelines (CONTRIBUTING.md)
  - UV setup guide (UV_SETUP.md)
  - Quick setup guide (SETUP.md)
- **PrettyTable Integration**: Diagnostic tables now use `prettytable` library for better formatted ASCII tables
- **Standard CLI Options**: All varlord-based applications now support standard command-line options:
  - `--help, -h`: Show help message and exit
  - `--check-variables, -cv`: Show diagnostic table of all configuration variables and exit
- **Enhanced Diagnostic Table**: `--check-variables` now displays two comprehensive tables:
  - **Variable Status Table**: Shows all configuration variables with their status (Required/Optional, Loaded/Missing, Source, Value)
  - **Source Information Table**: Shows detailed source diagnostics including:
    - Priority order (1 = lowest, higher numbers = higher priority)
    - Source name (from source.name property)
    - Instance (source string representation via str(source))
    - Load time in milliseconds (for performance diagnostics)
    - Watch support status (Yes/No)
    - Last update time (N/A for now, extensible for future use)
- **Improved Help Output**: Help text now includes standard options section at the beginning
- **Source Load Time Measurement**: Automatic measurement of source load times for performance diagnostics

### Changed
- **Help Output**: Removed "Configuration Source Priority" section from help output (moved to `--check-variables` for better visibility)
- **Diagnostic Output**: `--check-variables` now provides comprehensive source diagnostics in addition to variable status
- **Dependencies**: Added `prettytable>=3.0.0` as a core dependency for better table formatting

### Fixed
- Fixed `Env.__repr__()` to reflect model-based filtering (removed outdated `prefix` reference)
- Improved error messages when required fields are missing in `--check-variables` mode

## [0.2.0] - 2025-01-02

### Added
- **Explicit Required/Optional Configuration**: All fields must explicitly specify exactly one of `required=True` or `optional=True` in metadata. No inference allowed.
  - Missing both raises `ModelDefinitionError` with reason `"missing_metadata"`
  - Including both raises `ModelDefinitionError` with reason `"conflicting_metadata"`
  - Using `Optional[T]` type annotation raises `ModelDefinitionError` with reason `"optional_type"`
- **Automatic Model Defaults**: Model defaults are automatically applied as base layer. No need to explicitly include `sources.Defaults` in sources list.
- **Model-Driven Source Filtering**: All sources (Env, CLI, DotEnv, Etcd) now filter variables/arguments based on model fields. Only model-defined fields are loaded.
- **Required Field Validation**: New `Config.validate()` method to validate required fields independently. `Config.load()` now has optional `validate` parameter.
- **Comprehensive Error Messages**: When required fields are missing, error messages include:
  - List of missing fields with descriptions
  - Source mapping rules and examples for each active source
  - Actionable guidance on how to provide missing parameters
- **Field Metadata Support**: Support for `description` and `help` in field metadata for better documentation and CLI help text.
- **New Modules**:
  - `varlord.metadata`: Field information extraction and utilities
  - `varlord.validation`: Model definition validation and configuration validation
  - `varlord.source_help`: Source mapping examples and error message formatting

### Changed
- **BREAKING**: `Env` source no longer accepts `prefix` parameter. All environment variables are filtered by model fields.
- **BREAKING**: All fields must have explicit `required` or `optional` metadata. `ModelDefinitionError` is raised if missing.
- **BREAKING**: `Config.from_model()` no longer accepts `env_prefix` parameter.
- **BREAKING**: `Defaults` source is now internal. Model defaults are automatically applied, no need to include in sources list.
- **BREAKING**: Empty strings and empty collections are now considered valid values for required fields (only presence is checked, not emptiness).

### Fixed
- Improved error messages for missing required fields
- Better CLI help text with field descriptions
- Consistent model filtering across all sources

## [0.1.0] - 2025-12-31

### Added
- Comprehensive tutorial
- Comprehensive documentation

## [0.0.1] - 2025-12-30

### Added
- Initial project setup
- Core Source abstraction
- Defaults, DotEnv, Env, CLI sources
- ConfigStore with dynamic updates
- PriorityPolicy for customizable priority ordering
- Optional etcd integration
- Type conversion system
- Configuration validation framework
- Nested configuration support
- Built-in validators module with 30+ validators
- Unified key mapping and case normalization across all sources
- Nested configuration support with automatic type conversion
- Dynamic configuration updates with ConfigStore
- PriorityPolicy for per-key priority rules
- Custom source support

