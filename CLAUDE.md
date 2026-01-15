# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Development Setup
```bash
# Recommended for active development (installs package + all dependencies)
make dev-install

# Alternative: dependencies only (for CI/CD or when you only need tools)
make setup-venv
```

### Testing
```bash
make test              # Run all unit tests (excludes integration tests)
make test-cov          # Run tests with coverage report
make test-integration  # Run all integration tests (requires external services)
make test-etcd         # Run etcd integration tests (requires running etcd instance)
make test-dotenv       # Run dotenv integration tests
```

### Code Quality
```bash
make lint          # Run linting checks (ruff)
make format        # Format code with ruff
make format-check  # Check code formatting
make check         # Run all checks (lint + format check + tests)
```

### Building and Publishing
```bash
make build         # Build source and wheel distributions
make check-package # Check package before uploading
make upload        # Upload to PyPI (requires PYPI_TOKEN env var)
make upload-test   # Upload to TestPyPI (requires TEST_PYPI_TOKEN env var)
```

### Documentation
```bash
make docs          # Build documentation (in docs/ directory)
```

### Running a Single Test
```bash
# Run specific test file
pytest tests/test_config.py -v

# Run specific test class
pytest tests/test_config.py::TestConfig -v

# Run specific test function
pytest tests/test_config.py::TestConfig::test_load -v

# Run with specific markers
pytest tests/ -v -m etcd              # etcd tests only
pytest tests/ -v -m integration       # all integration tests
pytest tests/ -v -m "not integration" # unit tests only
```

## High-Level Architecture

Varlord is a Python configuration management library built around three core abstractions:

### Core Components

1. **Config (`varlord/config.py`)**: Main entry point that orchestrates configuration loading. It:
   - Takes a dataclass model and a list of sources
   - Auto-injects the model to all sources (no need to pass model to sources)
   - Automatically creates a Defaults source from model defaults
   - Merges sources using the Resolver
   - Converts the merged dict back to a model instance

2. **Source (`varlord/sources/base.py`)**: Abstract base class for configuration sources. All sources:
   - Implement `load()` to return a Mapping[str, Any]
   - Have a `name` property for identification
   - Have a unique `id` for precise source identification
   - Optionally implement `watch()` for dynamic updates
   - Support model-based field filtering (auto-injected)

3. **Resolver (`varlord/resolver.py`)**: Merges configuration from multiple sources:
   - Simple priority rule: later sources override earlier ones
   - Optional PriorityPolicy for per-key priority rules
   - Uses `normalize_key()` to convert keys (e.g., `DB__HOST` → `db.host`)

4. **ConfigStore (`varlord/store.py`)**: For dynamic configuration updates:
   - Thread-safe concurrent access
   - Subscribe to change notifications
   - Uses watch-enabled sources for real-time updates

### Key Design Patterns

- **Model-driven filtering**: Each source automatically filters by model fields - no prefix management needed
- **Automatic defaults**: Model defaults are extracted and used as the base layer automatically
- **Flat to nested conversion**: Sources return flat dicts with dot notation (`db.host`), Config converts to nested structure matching the model
- **Key normalization**: `normalize_key()` in `sources/base.py` applies consistent rules:
  - Double underscores (`__`) → dots (`.`) for nesting
  - Keys converted to lowercase
  - Single underscores preserved

### Source Priority Order

```
Defaults (auto) < User sources (order specified) < CLI (if included)
```

When using `Config.from_model()`: Defaults < Env < DotEnv < Etcd < CLI

### Module Structure

- `varlord/config.py` - Main Config class
- `varlord/sources/` - All source implementations
- `varlord/resolver.py` - Merges multiple sources
- `varlord/store.py` - Dynamic updates with ConfigStore
- `varlord/metadata.py` - Field info extraction from dataclasses
- `varlord/converters.py` - Type conversion (string → int/bool/float/etc)
- `varlord/validators.py` - Validation utilities
- `varlord/model_validation.py` - Model and config validation
- `varlord/policy.py` - PriorityPolicy for per-key priority rules
- `varlord/exporters.py` - Export config to JSON/YAML/TOML/ENV
- `varlord/global_config.py` - Global config management (optional feature)
- `varlord/logging.py` - Internal logging utilities

### Testing Structure

Tests are organized into:
- **Unit tests** (`test_*.py`): Fast, no external dependencies
- **Integration tests** (marked `@pytest.mark.integration`): Require external services
  - **Etcd tests** (marked `@pytest.mark.etcd`): Require running etcd instance
  - **Dotenv tests** (marked `@pytest.mark.requires_dotenv`): Require python-dotenv

By default, `pytest` runs only unit tests (excludes integration tests).

### Optional Dependencies

The library has optional extras:
- `dotenv` - python-dotenv for .env file support
- `etcd` - etcd3 for etcd key-value store support

Sources that require optional dependencies gracefully degrade if not installed (check with `try/except ImportError` in `sources/__init__.py`).

### Model Requirements

All dataclass fields MUST have explicit metadata:
```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Config:
    required_field: str = field(metadata={"description": "Required field"})
    optional_field: str = field(default="default", metadata={"description": "Optional field"})
```

This is enforced by `validate_model_definition()` in `model_validation.py`.

### CLI Integration

The `Config` class provides built-in CLI support:
- `handle_cli_commands()` - Handles `--help/-h` and `--check-variables/-cv`
- Auto-generates help from model metadata
- Shows diagnostic tables with variable status, source priority, and load times

Call `cfg.handle_cli_commands()` before `cfg.load()` to enable CLI features.

### Thread Safety

- `Config.load()` is not thread-safe (one-time load)
- `ConfigStore` is thread-safe for dynamic updates
- Sources should be immutable after initialization (frozen dataclasses preferred)
