# Varlord ⚙️

[![PyPI version](https://img.shields.io/pypi/v/varlord.svg)](https://pypi.org/project/varlord/)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Documentation](https://readthedocs.org/projects/varlord/badge/?version=latest)](https://varlord.readthedocs.io)

**Varlord** is a powerful Python configuration management library that provides a unified interface for loading configuration from multiple sources with customizable priority ordering and optional dynamic updates via etcd.

## ✨ Features

- 🔧 **Multiple Sources**: Support for defaults (automatic), CLI arguments, environment variables, `.env` files, and optional etcd integration
- 🎯 **Simple Priority**: Priority determined by sources order (later overrides earlier)
- 🔄 **Dynamic Updates**: Real-time configuration updates via etcd watch (optional)
- 🛡️ **Type Safety**: Built-in support for dataclass models with automatic type conversion
- 📝 **Logging Support**: Configurable logging to track configuration loading and merging
- ✅ **Validation Framework**: Built-in value validators and required field validation with comprehensive error messages
- 🔍 **Model-Driven Filtering**: All sources automatically filter by model fields - no prefix needed
- 🔌 **Pluggable Architecture**: Clean source abstraction for easy extension
- 📦 **Optional Dependencies**: Lightweight core with optional extras for dotenv and etcd
- 🚀 **Production Ready**: Thread-safe, fail-safe update strategies, and comprehensive error handling
- 🎨 **Simple API**: Convenience methods and auto-injection for cleaner code

## 📦 Installation

### Basic Installation

```bash
pip install varlord
```

### With Optional Dependencies

```bash
# With .env file support
pip install varlord[dotenv]

# With etcd support
pip install varlord[etcd]

# With all optional dependencies
pip install varlord[dotenv,etcd]

# Development installation
pip install -e ".[dev]"
```

## 🚀 Quick Start

### Basic Usage

```python
from dataclasses import dataclass, field
from varlord import Config, sources

@dataclass(frozen=True)
class AppConfig:
    host: str = field(default="127.0.0.1", metadata={"optional": True})
    port: int = field(default=8000, metadata={"optional": True})
    debug: bool = field(default=False, metadata={"optional": True})

# Model defaults are automatically applied - no need for sources.Defaults
# Sources filter by model fields automatically
cfg = Config(
    model=AppConfig,
    sources=[
        sources.Env(),        # HOST, PORT, DEBUG (filtered by model)
        sources.CLI(),        # --host, --port, --debug (model auto-injected)
    ],
)

app = cfg.load()
print(app.host)  # Can be overridden by env var or CLI arg
print(app.port)
```

### Convenience Method

```python
# One-line setup for common cases
cfg = Config.from_model(
    AppConfig,
    cli=True,
    dotenv=".env",
)

app = cfg.load()
```

### Priority Ordering

**Method 1: Reorder sources (recommended - simplest)**
```python
# Priority is determined by sources order: later sources override earlier ones
# Model defaults are automatically applied first (lowest priority)
cfg = Config(
    model=AppConfig,
    sources=[
        sources.Env(),  # Overrides defaults
        sources.CLI(),  # Highest priority (overrides env)
    ],
)
```

**Method 2: Use PriorityPolicy (advanced: per-key rules)**
```python
from varlord import PriorityPolicy

# Use when you need different priority rules for different keys
cfg = Config(
    model=AppConfig,
    sources=[...],
    policy=PriorityPolicy(
        default=["defaults", "env", "cli"],  # Default order for all keys
        overrides={
            "secrets.*": ["defaults", "etcd"],  # Secrets: skip env, only etcd can override
        }
    ),
)
```

### Dynamic Updates with Etcd

```python
def on_change(new_config, diff):
    print("Config updated:", diff)

cfg = Config(
    model=AppConfig,
    sources=[
        sources.Env(),  # Defaults applied automatically
        sources.Etcd("http://127.0.0.1:2379", prefix="/app/", watch=True),
    ],
)

store = cfg.load_store()  # Automatically enables watch if sources support it
store.subscribe(on_change)

current = store.get()  # Thread-safe access to current config
```

### Logging

Enable debug logging to track configuration loading:

```python
import logging
from varlord import set_log_level

set_log_level(logging.DEBUG)
cfg = Config(...)
app = cfg.load()  # Logs source loads, merges, type conversions
```

### Validation

**Value Validation**: Add validators in your model's ``__post_init__``:

```python
from dataclasses import dataclass, field
from varlord.validators import validate_range, validate_regex

@dataclass(frozen=True)
class AppConfig:
    port: int = field(default=8000, metadata={"optional": True})
    host: str = field(default="127.0.0.1", metadata={"optional": True})

    def __post_init__(self):
        validate_range(self.port, min=1, max=65535)
        validate_regex(self.host, r'^\d+\.\d+\.\d+\.\d+$')
```

**Required Field Validation**: All fields must explicitly specify ``metadata={"required": True}`` or ``metadata={"optional": True}``:

```python
from dataclasses import dataclass, field
from varlord.model_validation import RequiredFieldError

@dataclass(frozen=True)
class AppConfig:
    api_key: str = field(metadata={"required": True})  # Must be provided
    host: str = field(default="127.0.0.1", metadata={"optional": True})

cfg = Config(model=AppConfig, sources=[])
try:
    app = cfg.load()  # Raises RequiredFieldError if api_key not provided
except RequiredFieldError as e:
    print(f"Missing required fields: {e.missing_fields}")
```

## 📚 Documentation

Full documentation is available at [https://varlord.readthedocs.io](https://varlord.readthedocs.io)

- **Latest**: [https://varlord.readthedocs.io/en/latest/](https://varlord.readthedocs.io/en/latest/)
- **Stable**: [https://varlord.readthedocs.io/en/stable/](https://varlord.readthedocs.io/en/stable/)

## 🎯 Key Concepts

### Configuration Model

Use dataclass to define your configuration structure with type hints and default values.

### Sources

Each source implements a unified interface:
- `load() -> Mapping[str, Any]`: Load configuration snapshot
- `watch() -> Iterator[ChangeEvent]` (optional): Stream of changes for dynamic updates
- `name`: Source name for identification

### Priority Ordering

**Simple (Recommended)**: Reorder sources list - later sources override earlier ones.

**Advanced**: Use `PriorityPolicy` for per-key priority rules (e.g., different rules for secrets).

### Type Conversion

Automatic conversion from strings (env vars, CLI) to model field types (int, float, bool, etc.).

### Validation

**Value Validation**: Add validators in your model's `__post_init__` method to validate configuration values.

**Required Field Validation**: All fields must explicitly specify `metadata={"required": True}` or `metadata={"optional": True}`. Required fields are automatically validated before `__post_init__` is called.

### ConfigStore

Runtime configuration management with:
- Thread-safe atomic snapshots
- Dynamic updates via watch mechanism
- Change subscriptions

## 🏢 About Agentsmith

**Varlord** is part of the **Agentsmith** open-source ecosystem. Agentsmith is a ToB AI agent and algorithm development platform, currently deployed in multiple highway management companies, securities firms, and regulatory agencies in China. The Agentsmith team is gradually open-sourcing the platform by removing proprietary code and algorithm modules, as well as enterprise-specific customizations, while decoupling the system for modular use by the open-source community.

### 🌟 Agentsmith Open-Source Projects

- **[Varlord](https://github.com/lzjever/varlord)** ⚙️ - Configuration management library with multi-source support
- **[Routilux](https://github.com/lzjever/routilux)** ⚡ - Event-driven workflow orchestration framework
- **[Serilux](https://github.com/lzjever/serilux)** 📦 - Flexible serialization framework for Python objects
- **[Lexilux](https://github.com/lzjever/lexilux)** 🚀 - Unified LLM API client library

These projects are modular components extracted from the Agentsmith platform, designed to be used independently or together to build powerful applications.


## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.
