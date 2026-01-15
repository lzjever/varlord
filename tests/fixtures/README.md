# Test Fixtures

This directory contains test data files used by varlord tests.

## Directory Structure

```
fixtures/
├── yaml/           # YAML configuration files
├── json/           # JSON configuration files
├── toml/           # TOML configuration files
└── env/            # Environment variable files
```

## Usage

Tests can use these fixtures with pytest's `datadir` plugin:

```python
def test_yaml_load_valid(datadir):
    from varlord.sources import YAML
    source = YAML(str(datadir / "yaml" / "config_valid.yaml"))
    result = source.load()
    assert result["database.host"] == "localhost"
```

## Files

### YAML Files
- `config_valid.yaml` - Valid YAML with nested structure
- `config_invalid_syntax.yaml` - Invalid YAML for error testing
- `config_nested.yaml` - Deeply nested configuration

### JSON Files
- `config_valid.json` - Valid JSON configuration

### TOML Files
- `config_valid.toml` - Valid TOML configuration

### ENV Files
- `test_config.env` - Environment variables for testing

## Adding New Fixtures

When adding new test data files:
1. Choose appropriate subdirectory (yaml/json/toml/env)
2. Use descriptive names (e.g., `config_valid.yaml`, `config_invalid.yaml`)
3. Keep files simple and focused on specific test scenarios
4. Update this README if adding new categories
