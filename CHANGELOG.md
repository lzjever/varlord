# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - Unreleased

### Added
- **PrettyTable Integration**: Diagnostic tables now use `prettytable` library for better formatted ASCII tables
- **Standard CLI Options**: All varlord-based applications now support standard command-line options:
  - `--help, -h`: Show help message and exit
  - `--check-variables, -cv`: Show diagnostic table of all configuration variables and exit
- **Enhanced Diagnostic Table**: `--check-variables` now displays two comprehensive tables:
  - **Variable Status Table**: Shows all configuration variables with their status (Required/Optional, Loaded/Missing, Source, Value)
  - **Source Information Table**: Shows detailed source diagnostics including:
    - Priority order (1 = lowest, higher numbers = higher priority)
    - Source name (readable format)
    - Source parameters (e.g., path, host, port, watch settings)
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

