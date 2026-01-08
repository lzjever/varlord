# Varlord Examples

This directory contains example scripts demonstrating various features of Varlord.

## Examples

### 1. `basic_example.py` - Basic Usage
Demonstrates the most common use case: loading configuration from defaults, environment variables, and CLI arguments.

**Features:**
- Required and optional fields
- Multiple sources (Env, CLI)
- Friendly error messages
- Check-variables support

**Run:**
```bash
python basic_example.py --api-key your_key
python basic_example.py -cv  # Check variables
python basic_example.py --help  # Show help
```

### 2. `validation_example.py` - Configuration Validation
Shows how to use validators to ensure configuration values meet your requirements.

**Features:**
- Field validation with `validate_range()` and `validate_regex()`
- Validation error handling
- Check-variables support

**Run:**
```bash
python validation_example.py
python validation_example.py --port 99999  # Will fail validation
python validation_example.py -cv
```

### 3. `priority_example.py` - Priority Ordering
Demonstrates three ways to customize priority:
1. Reorder sources (recommended - simplest)
2. Use PriorityPolicy for per-key rules
3. Multiple sources of the same type with custom IDs

**Features:**
- Source ordering
- PriorityPolicy with per-key rules
- Multiple YAML sources with different priorities
- Source ID system

**Run:**
```bash
python priority_example.py
python priority_example.py --host 0.0.0.0 --port 9999
```

### 4. `nested_validation_example.py` - Nested Configuration
Shows nested dataclass structures with validation at multiple levels.

**Features:**
- Nested dataclass structures (best practice)
- Multi-level validation
- Cross-field validation
- Environment variable mapping (DB__HOST → db.host)

**Run:**
```bash
python nested_validation_example.py
python nested_validation_example.py -cv
```

### 5. `logging_example.py` - Logging and Diagnostics
Demonstrates logging support and diagnostic features.

**Features:**
- Debug logging
- Check-variables with detailed source information
- Source status tracking

**Run:**
```bash
python logging_example.py
python logging_example.py -cv  # Check variables with detailed info
```

### 6. `file_sources_example.py` - File-Based Sources
Demonstrates loading configuration from YAML, JSON, and TOML files.

**Features:**
- YAML, JSON, TOML sources
- Multiple file sources with priority
- Nested configuration structures
- Missing file handling (graceful degradation)

**Run:**
```bash
python file_sources_example.py
python file_sources_example.py -cv
```

## Best Practices Demonstrated

### 1. Nested Configuration
✅ **Use nested dataclasses:**
```python
@dataclass(frozen=True)
class DBConfig:
    host: str = field(default="localhost")
    port: int = field(default=5432)

@dataclass(frozen=True)
class AppConfig:
    db: DBConfig = field(default_factory=DBConfig)
```

❌ **Avoid double underscores:**
```python
# Don't do this
db__host: str = field(...)
```

### 2. Field Metadata
Always include descriptions for better error messages:
```python
host: str = field(
    default="127.0.0.1",
    metadata={"description": "Server host address"}
)
```

### 3. Error Handling
Use `RequiredFieldError` for friendly error messages:
```python
from varlord.model_validation import RequiredFieldError

try:
    app = cfg.load()
except RequiredFieldError as e:
    print(f"Error: {e}")  # Shows field descriptions
```

### 4. Source Ordering
Priority is determined by source order (later sources override earlier ones):
```python
cfg = Config(
    model=AppConfig,
    sources=[
        sources.Env(),   # Lower priority
        sources.CLI(),   # Higher priority (overrides Env)
    ],
)
```

### 5. Check Variables
Always support `-cv` flag for diagnostics:
```python
cfg.handle_cli_commands()  # Handles --help, -cv, etc.
```

## Running All Examples

To run all examples:
```bash
for example in examples/*.py; do
    echo "Running $example..."
    python "$example"
    echo ""
done
```

## Common Patterns

### Pattern 1: Basic App Configuration
```python
from dataclasses import dataclass, field
from varlord import Config, sources

@dataclass(frozen=True)
class AppConfig:
    host: str = field(default="127.0.0.1")
    port: int = field(default=8000)

cfg = Config(
    model=AppConfig,
    sources=[sources.Env(), sources.CLI()],
)
cfg.handle_cli_commands()
app = cfg.load()
```

### Pattern 2: Nested Configuration
```python
@dataclass(frozen=True)
class DBConfig:
    host: str = field(default="localhost")
    port: int = field(default=5432)

@dataclass(frozen=True)
class AppConfig:
    db: DBConfig = field(default_factory=DBConfig)

# Environment: DB__HOST=db.example.com DB__PORT=3306
# CLI: --db-host db.example.com --db-port 3306
```

### Pattern 3: File-Based Configuration
```python
cfg = Config(
    model=AppConfig,
    sources=[
        sources.YAML("/etc/app/config.yaml", model=AppConfig),  # System config
        sources.YAML("~/.config/app.yaml", model=AppConfig),     # User config
        sources.Env(),
        sources.CLI(),
    ],
)
```

### Pattern 4: Validation
```python
from varlord.validators import validate_range, validate_regex

@dataclass(frozen=True)
class AppConfig:
    port: int = field(default=8000)

    def __post_init__(self):
        validate_range(self.port, min=1, max=65535)
```

## Tips

1. **Always use `field()` with metadata** for better error messages
2. **Use nested dataclasses** instead of double underscores
3. **Handle `RequiredFieldError`** for user-friendly errors
4. **Support `-cv` flag** for diagnostics
5. **Use `default_factory`** for nested dataclasses
6. **Order sources by priority** (later = higher priority)
