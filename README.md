# Varlord ⚙️

[![PyPI version](https://img.shields.io/pypi/v/varlord.svg)](https://pypi.org/project/varlord/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Documentation](https://readthedocs.org/projects/varlord/badge/?version=latest)](https://varlord.readthedocs.io)
[![CI](https://github.com/lzjever/varlord/workflows/CI/badge.svg)](https://github.com/lzjever/varlord/actions)
[![codecov](https://codecov.io/gh/lzjever/varlord/branch/main/graph/badge.svg)](https://codecov.io/gh/lzjever/varlord)

> **Stop wrestling with configuration chaos. Start with Varlord.**

**Varlord** is a battle-tested Python configuration management library that eliminates the pain of managing configuration from multiple sources. Born from real-world production challenges, it provides a **unified, type-safe, and elegant** solution for configuration management.

## 🎯 The Problem We Solve

### Real-World Configuration Nightmares

Every Python developer has faced these frustrating scenarios:

#### ❌ **The Configuration Spaghetti**
```python
# Your code becomes a mess of conditionals and parsing
host = os.getenv("HOST", "127.0.0.1")
port = int(os.getenv("PORT", "8000"))  # What if PORT is not a number?
debug = os.getenv("DEBUG", "false").lower() == "true"  # Really?
if "--host" in sys.argv:
    host = sys.argv[sys.argv.index("--host") + 1]  # Error-prone parsing
# ... and it gets worse with nested configs, validation, etc.
```

#### ❌ **Priority Confusion**
> "Does CLI override env? Or env overrides CLI? Wait, what about the config file? Which one wins?"

#### ❌ **Type Conversion Hell**
```python
# String "true" vs boolean True vs "1" vs 1
# "8000" vs 8000
# Missing values, None handling, type errors at runtime...
```

#### ❌ **The Restart Tax**
> "I just need to change one config value. Why do I have to restart the entire service?"

#### ❌ **Silent Failures**
> "The config looks wrong, but the app starts anyway. Users report bugs 3 hours later."

### ✅ **Varlord's Solution**

**One unified interface. Multiple sources. Clear priority. Built-in diagnostics.**

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from varlord import Config, sources

@dataclass(frozen=True)
class AppConfig:
    """Application configuration with clear structure and validation."""
    
    # Required field - must be provided
    api_key: str = field(metadata={"description": "API key for authentication"})
    
    # Optional fields with sensible defaults
    host: str = field(default="127.0.0.1", metadata={"description": "Server host address"})
    port: int = field(default=8000, metadata={"description": "Server port number"})
    debug: bool = field(default=False, metadata={"description": "Enable debug mode"})
    timeout: float = field(default=30.0, metadata={"description": "Request timeout in seconds"})
    hello_message: Optional[str] = field(
        default=None, metadata={"description": "Optional greeting message"}
    )

def main():
    # Define configuration sources with clear priority order
    # Priority: CLI (highest) > User Config > App Config > System Config > Env > Defaults (lowest)
    cfg = Config(
        model=AppConfig,
        sources=[
            # System-wide configuration (lowest priority, rarely overridden)
            sources.YAML("/etc/myapp/config.yaml"),  # System config
            
            # Application-level configuration
            sources.JSON(Path(__file__).parent / "config.json"),  # App directory
            
            # User-specific configuration (overrides system and app configs)
            sources.YAML(Path.home() / ".config" / "myapp" / "config.yaml"),  # User directory
            sources.TOML(Path.home() / ".myapp.toml"),  # Alternative user config
            
            # Environment variables (common in containers/CI)
            sources.Env(),
            sources.DotEnv(".env"),  # Local development
            
            # Command-line arguments (highest priority, for debugging/overrides)
            sources.CLI(),
        ],
    )
    
    # One line to add comprehensive CLI management: --help, --check-variables, etc.
    # This single call adds:
    #   - --help / -h: Auto-generated help from your model metadata
    #   - --check-variables / -cv: Complete configuration diagnostics
    #   - Automatic validation and error reporting
    #   - Exit handling (exits if help/cv is requested)
    cfg.handle_cli_commands()  # Handles --help, -cv automatically, exits if needed
    
    # Load configuration - type-safe, validated, ready to use
    app = cfg.load()
    
    # Your application code
    print(f"Starting server on {app.host}:{app.port}")
    print(f"Debug: {app.debug}, Timeout: {app.timeout}s")

if __name__ == "__main__":
    main()
```

**What just happened?**

1. **✅ Multiple Sources, Unified Interface**: System config, app config, user config, env vars, CLI - all handled the same way
2. **✅ Clear Priority**: Later sources override earlier ones - no confusion
3. **✅ Automatic Type Conversion**: Strings from files/env → proper types (int, bool, float)
4. **✅ Model-Driven Filtering**: Each source only reads fields defined in your model
5. **✅ Built-in Diagnostics**: `--check-variables` shows exactly what's loaded from where
6. **✅ Zero Boilerplate**: No parsing, no type conversion code, no priority logic

**Try it:**

```bash
# See comprehensive configuration diagnostics
python app.py --check-variables
# or short form
python app.py -cv

# See help with all sources and priority
python app.py --help

# Run normally
python app.py --api-key your_key
```

**The `--check-variables` output shows everything:**

When you run `python app.py -cv`, you get a comprehensive diagnostic report:

```
+---------------+----------+---------------+----------+-----------+
| Variable      | Required | Status        | Source   | Value     |
+---------------+----------+---------------+----------+-----------+
| api_key       | Required | Missing       | defaults | None      |
| host          | Optional | Loaded        | dotenv   | localhost |
| port          | Optional | Loaded        | dotenv   | 7000      |
| debug         | Optional | Loaded        | dotenv   | true      |
| timeout       | Optional | Loaded        | dotenv   | 20.0      |
| hello_message | Optional | Using Default | defaults | None      |
+---------------+----------+---------------+----------+-----------+

Configuration Source Priority and Details:

+------------+-------------+-----------+----------------------------------------+--------+----------------+---------------+-------------+
| Priority   | Source Name | Source ID | Instance                               | Status | Load Time (ms) | Watch Support | Last Update |
+------------+-------------+-----------+----------------------------------------+--------+----------------+---------------+-------------+
| 1 (lowest) | defaults    | defaults  | <Defaults(model=AppConfig)>            | Active | 0.00           | No            | N/A         |
| 2          | yaml        | yaml      | <YAML(/etc/myapp/config.yaml)>         | Active | 0.15           | No            | N/A         |
| 3          | json        | json      | <JSON(config.json)>                    | Active | 0.08           | No            | N/A         |
| 4          | yaml        | yaml      | <YAML(~/.config/myapp/config.yaml)>    | Active | 0.12           | No            | N/A         |
| 5          | toml        | toml      | <TOML(~/.myapp.toml)>                  | Active | 0.05           | No            | N/A         |
| 6          | env         | env       | <Env(model-based)>                     | Active | 0.05           | No            | N/A         |
| 7          | dotenv      | dotenv    | <DotEnv(.env)>                         | Active | 0.03           | No            | N/A         |
| 8 (highest)| cli         | cli       | <CLI()>                                | Active | 0.20           | No            | N/A         |
+------------+-------------+-----------+----------------------------------------+--------+----------------+---------------+-------------+


Note: Later sources override earlier ones (higher priority).

⚠️  Missing required fields: api_key
   Exiting with code 1. Please provide these fields and try again.
   For help, run: python app.py --help
```

**What this tells you:**

- **Variable Status**: See which fields are required vs optional, loaded vs missing
- **Source Tracking**: Know exactly which source (defaults/env/cli/file) provided each value
- **Priority Order**: Understand the resolution chain - later sources override earlier
- **Performance**: Load times for each source (useful for optimization)
- **Validation**: Missing required fields are caught immediately with clear error messages

**Key Benefits:**

- **🔍 Complete Visibility**: See exactly which source provides each value - no more guessing where config comes from
- **📊 Priority Visualization**: Understand the resolution order at a glance - see which source wins for each field
- **⚡ Performance Metrics**: Load times for each source - identify slow config sources
- **🛡️ Validation**: Missing required fields are caught before app starts - fail fast with clear errors
- **📝 Self-Documenting**: Help text generated from your model metadata - no manual documentation needed
- **🎯 Zero Configuration**: `handle_cli_commands()` adds all this with one line - no boilerplate

**Real-World Scenarios:**

- **Debugging**: "Why is my app using the wrong port?" → `python app.py -cv` shows port comes from env, not CLI
- **Onboarding**: New team member runs `python app.py --help` → sees all config options with descriptions
- **CI/CD**: Missing required field? → `-cv` shows exactly what's missing before deployment fails
- **Multi-Environment**: See which config file (system/user/app) is actually being used

**That's it.** No parsing, no type conversion, no priority confusion. Just clean, type-safe configuration with built-in diagnostics.

---

## 🌟 Why Varlord?

### 🎯 **Core Value Propositions**

| Problem | Varlord Solution | Impact |
|---------|-----------------|--------|
| **Config scattered everywhere** | Unified interface for all sources | Single source of truth |
| **Priority confusion** | Simple rule: later sources override earlier | Predictable behavior |
| **Type conversion errors** | Automatic conversion with validation | Catch errors early |
| **No runtime updates** | Optional etcd watch for dynamic updates | Zero-downtime config changes |
| **Repetitive boilerplate** | Model-driven, auto-filtering | 90% less code |
| **Silent failures** | Built-in validation framework | Fail fast, fail clear |

### 💡 **Key Differentiators**

1. **🎯 Model-Driven Design**: Define your config once as a dataclass, and Varlord handles the rest
2. **🔄 Smart Auto-Filtering**: Sources automatically filter by model fields - no prefix management needed
3. **⚡ Zero Boilerplate**: Model defaults are automatic, model is auto-injected to sources
4. **🛡️ Type Safety First**: Full type hints support with automatic conversion and validation
5. **🚀 Production Ready**: Thread-safe, fail-safe, battle-tested in production environments

---

## 🚀 Quick Start

### Installation

```bash
pip install varlord

# With optional features
pip install varlord[dotenv,etcd]
```

### Basic Usage (30 seconds)

```python
from dataclasses import dataclass, field
from varlord import Config, sources

@dataclass(frozen=True)
class AppConfig:
    host: str = field(default="127.0.0.1")
    port: int = field(default=8000)
    debug: bool = field(default=False)

# Create config - that's it!
cfg = Config(
    model=AppConfig,
    sources=[
        sources.Env(),   # Reads HOST, PORT, DEBUG from environment
        sources.CLI(),   # Reads --host, --port, --debug from CLI
    ],
)

app = cfg.load()  # Type-safe, validated config object
print(f"Server: {app.host}:{app.port}, Debug: {app.debug}")
```

**Run it:**
```bash
# Use defaults
python app.py
# Output: Server: 127.0.0.1:8000, Debug: False

# Override with env
export HOST=0.0.0.0 PORT=9000
python app.py
# Output: Server: 0.0.0.0:9000, Debug: False

# Override with CLI (highest priority)
python app.py --host 192.168.1.1 --port 8080 --debug
# Output: Server: 192.168.1.1:8080, Debug: True
```

### One-Liner Convenience Method

```python
# Even simpler for common cases
cfg = Config.from_model(AppConfig, cli=True, dotenv=".env")
app = cfg.load()
```

---

## 💼 Real-World Use Cases

### Use Case 1: Microservice Configuration

**Problem**: Your microservice needs config from multiple sources, and you're tired of writing parsing code.

**Solution**:
```python
@dataclass(frozen=True)
class ServiceConfig:
    db_host: str = field(default="localhost")
    db_port: int = field(default=5432)
    api_key: str = field()  # Required - must be provided
    log_level: str = field(default="INFO")
    max_workers: int = field(default=4)

cfg = Config(
    model=ServiceConfig,
    sources=[
        sources.Env(),           # Production: from environment
        sources.DotEnv(".env"),  # Development: from .env file
        sources.CLI(),           # Override: from command line
    ],
)

config = cfg.load()  # Validated, type-safe, ready to use
```

**Benefits**:
- ✅ Same code works in dev (`.env`), staging (env vars), and prod (env vars)
- ✅ CLI overrides for debugging: `python service.py --log-level DEBUG`
- ✅ Type safety: `max_workers` is always an `int`, never a string
- ✅ Validation: Missing `api_key` fails fast with clear error

### Use Case 2: Dynamic Configuration Updates

**Problem**: You need to change configuration without restarting the service.

**Solution**:
```python
def on_config_change(new_config, diff):
    print(f"Config updated: {diff}")
    # Update your app's behavior based on new config

cfg = Config(
    model=AppConfig,
    sources=[
        sources.Env(),
        sources.Etcd(
            host="etcd.example.com",
            prefix="/app/config/",
            watch=True,  # Enable dynamic updates
        ),
    ],
)

store = cfg.load_store()  # Returns ConfigStore for dynamic updates
store.subscribe(on_config_change)

# Thread-safe access to current config
current = store.get()
```

**Benefits**:
- ✅ Zero-downtime configuration updates
- ✅ Thread-safe concurrent access
- ✅ Automatic validation on updates
- ✅ Change notifications via callbacks

### Use Case 3: Multi-Environment Deployment

**Problem**: Different configs for dev, staging, and production, but you want one codebase.

**Solution**:
```python
# Development: .env file
# Staging: Environment variables
# Production: etcd + environment variables

cfg = Config(
    model=AppConfig,
    sources=[
        sources.DotEnv(".env"),  # Dev only (file may not exist in prod)
        sources.Env(),            # All environments
        sources.Etcd.from_env() if os.getenv("ETCD_HOST") else None,  # Prod only
        sources.CLI(),           # Override for debugging
    ],
)
```

**Benefits**:
- ✅ One codebase, multiple environments
- ✅ Environment-specific sources automatically handled
- ✅ Clear priority: CLI > etcd > env > .env > defaults

### Use Case 4: Complex Nested Configuration

**Problem**: Your config has nested structures (database, cache, API keys, etc.).

**Solution**:
```python
@dataclass(frozen=True)
class DatabaseConfig:
    host: str = field(default="localhost")
    port: int = field(default=5432)
    name: str = field(default="mydb")

@dataclass(frozen=True)
class AppConfig:
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    api_key: str = field()
    cache_ttl: int = field(default=3600)

cfg = Config(
    model=AppConfig,
    sources=[
        sources.Env(),  # Reads DB__HOST, DB__PORT, DB__NAME automatically
        sources.CLI(),  # Reads --db-host, --db-port, etc.
    ],
)

config = cfg.load()
# Access: config.db.host, config.db.port, config.api_key
```

**Benefits**:
- ✅ Automatic nested key mapping (`DB__HOST` → `db.host`)
- ✅ Type-safe nested access
- ✅ Validation at all levels

---

## 🎨 Key Features

### 1. **Multiple Sources, Unified Interface**

```python
sources = [
    sources.Defaults(),      # From model defaults (automatic)
    sources.Env(),           # From environment variables
    sources.CLI(),           # From command-line arguments
    sources.DotEnv(".env"),  # From .env files
    sources.YAML("config.yaml"),  # From YAML files
    sources.TOML("config.toml"),  # From TOML files
    sources.Etcd(...),       # From etcd (optional)
]
```

### 2. **Simple Priority Rule**

> **Later sources override earlier ones. That's it.**

```python
cfg = Config(
    model=AppConfig,
    sources=[
        sources.Env(),   # Priority 1 (lowest)
        sources.CLI(),   # Priority 2 (highest - overrides env)
    ],
)
```

### 3. **Automatic Type Conversion**

```python
# Environment variables are strings, but Varlord converts them automatically
export PORT=9000 DEBUG=true TIMEOUT=30.5

@dataclass(frozen=True)
class Config:
    port: int = 8000        # "9000" → 9000
    debug: bool = False     # "true" → True
    timeout: float = 30.0   # "30.5" → 30.5
```

### 4. **Model-Driven Filtering**

```python
# Your model defines what config you need
@dataclass(frozen=True)
class Config:
    host: str = "127.0.0.1"
    port: int = 8000
    # ... only these fields

# Sources automatically filter - no prefix management needed
# Env source only reads HOST and PORT, ignores everything else
# CLI source only parses --host and --port, ignores other args
```

### 5. **Built-in Validation**

```python
from varlord.validators import validate_range, validate_regex

@dataclass(frozen=True)
class Config:
    port: int = field(default=8000)
    host: str = field(default="127.0.0.1")
    
    def __post_init__(self):
        validate_range(self.port, min=1, max=65535)
        validate_regex(self.host, r'^\d+\.\d+\.\d+\.\d+$')
```

### 6. **Dynamic Updates (Optional)**

```python
store = cfg.load_store()  # Enable watch if sources support it
store.subscribe(lambda new_config, diff: print(f"Updated: {diff}"))

# Config updates automatically in background
# Thread-safe access: current = store.get()
```

---

## 📚 Documentation

- **📖 Full Documentation**: [https://varlord.readthedocs.io](https://varlord.readthedocs.io)
- **🚀 Quick Start Guide**: [Quick Start](https://varlord.readthedocs.io/en/latest/user_guide/quickstart.html)
- **💡 Examples**: [Examples Directory](examples/)
- **🎯 API Reference**: [API Documentation](https://varlord.readthedocs.io/en/latest/api/index.html)

---

## 🧠 Memory Aids (Quick Reference)

### The Varlord Mantra

> **"Define once, use everywhere. Later overrides earlier. Types are automatic."**

### Priority Cheat Sheet

```
Defaults < .env < Environment < YAML/TOML < etcd < CLI
  (lowest priority)                          (highest priority)
```

### Common Patterns

```python
# Pattern 1: Simple (most common)
Config(model=AppConfig, sources=[sources.Env(), sources.CLI()])

# Pattern 2: With .env file
Config(model=AppConfig, sources=[sources.DotEnv(".env"), sources.Env(), sources.CLI()])

# Pattern 3: Dynamic updates
Config(model=AppConfig, sources=[sources.Env(), sources.Etcd(..., watch=True)])
store = cfg.load_store()

# Pattern 4: One-liner
Config.from_model(AppConfig, cli=True, dotenv=".env")
```

---

## 🏢 Production Proven

**Varlord** is part of the **Agentsmith** ecosystem, battle-tested in production environments:

- ✅ Deployed in multiple highway management companies
- ✅ Used by securities firms and regulatory agencies
- ✅ Handles high-throughput microservices
- ✅ Thread-safe and production-ready

### 🌟 Agentsmith Open-Source Projects

- **[Varlord](https://github.com/lzjever/varlord)** ⚙️ - Configuration management (this project)
- **[Routilux](https://github.com/lzjever/routilux)** ⚡ - Event-driven workflow orchestration
- **[Serilux](https://github.com/lzjever/serilux)** 📦 - Flexible serialization framework
- **[Lexilux](https://github.com/lzjever/lexilux)** 🚀 - Unified LLM API client

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

Licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

---

## 🎯 TL;DR

**Varlord solves configuration management once and for all:**

1. ✅ **Define your config as a dataclass** - type-safe, validated
2. ✅ **Add sources in priority order** - later overrides earlier
3. ✅ **Call `load()`** - get a type-safe config object
4. ✅ **Optional: Enable dynamic updates** - zero-downtime config changes

**No more parsing. No more type conversion. No more priority confusion.**

```python
# Before: 50+ lines of parsing, type conversion, validation
# After: 3 lines
cfg = Config(model=AppConfig, sources=[sources.Env(), sources.CLI()])
app = cfg.load()
```

**That's the Varlord promise. 🚀**
