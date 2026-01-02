# Testing Guide

This document describes the testing structure and how to run tests for the varlord project.

## Test Structure

The test suite is organized into several categories:

- **Unit Tests**: Fast, isolated tests that don't require external services
- **Integration Tests**: Tests that require external services (marked with `@pytest.mark.integration`)
- **Etcd Tests**: Tests that require a running etcd instance (marked with `@pytest.mark.etcd`)

## Running Tests

### Run All Unit Tests (Default)

```bash
make test
# or
pytest tests/ -v
```

This runs all tests except integration tests (which are excluded by default in `pytest.ini`).

### Run All Tests Including Integration

```bash
make test-integration
# or
pytest tests/ -v -m integration
```

### Run Only Etcd Tests

```bash
make test-etcd
# or
pytest tests/ -v -m etcd
```

### Run Tests with Coverage

```bash
make test-cov
# or
pytest tests/ --cov=varlord --cov-report=html --cov-report=term
```

### Run Specific Test Files

```bash
# Run etcd integration tests
pytest tests/test_sources_etcd_integration.py -v -m etcd

# Run etcd watch tests
pytest tests/test_etcd_watch_integration.py -v -m etcd

# Run specific test class
pytest tests/test_config.py::TestConfig -v
```

## Etcd Integration Tests

### Prerequisites

1. **Running etcd instance**: You need a running etcd instance with TLS authentication enabled.

2. **Certificates**: You need the following certificate files:
   - CA certificate (e.g., `./cert/AgentsmithLocal.cert.pem`)
   - Client key (e.g., `./cert/etcd-client-lzj-local/key.pem`)
   - Client certificate (e.g., `./cert/etcd-client-lzj-local/cert.pem`)

3. **Python dependencies**: Install etcd support:
   ```bash
   pip install varlord[etcd]
   # or with uv
   uv sync --all-extras
   ```

### Configuration

You can configure the etcd connection via environment variables:

```bash
export ETCD_HOST=127.0.0.1
export ETCD_PORT=2379
export ETCD_CA_CERT=./cert/AgentsmithLocal.cert.pem
export ETCD_CERT_KEY=./cert/etcd-client-lzj-local/key.pem
export ETCD_CERT_CERT=./cert/etcd-client-lzj-local/cert.pem
```

### Testing Connection

Before running the full test suite, verify your connection works:

```bash
make test-etcd-connection
# or
python tests/test_etcd_connection.py
```

This script will:
- Check if certificates exist
- Test the etcd connection
- Verify the varlord Etcd source works

### Running Etcd Tests

#### Run all etcd integration tests:

```bash
make test-etcd
# or
pytest tests/test_sources_etcd_integration.py -v -m etcd
```

#### Run etcd watch tests:

```bash
pytest tests/test_etcd_watch_integration.py -v -m etcd
```

#### Run all integration tests (including etcd):

```bash
make test-integration
# or
pytest -m integration
```

#### Run all tests except integration tests (default):

```bash
pytest
# or explicitly:
pytest -m "not integration"
```

### Test Coverage

The etcd integration tests cover:

1. **Basic Functionality**:
   - Creating etcd source with TLS
   - Loading empty etcd
   - Loading simple key-value pairs
   - Loading nested keys (with `__` separator)
   - Loading keys with slash separator
   - Loading JSON values
   - Prefix filtering
   - Model field filtering

2. **Watch Functionality**:
   - Enabling/disabling watch
   - Watching for PUT events (add/modify)
   - Watching for DELETE events
   - Multiple keys watching
   - ConfigStore integration with watch
   - Subscribe callbacks with watch

3. **Integration**:
   - Using etcd source with Config class
   - Multiple sources with etcd
   - Priority ordering with etcd
   - Dynamic updates with ConfigStore
   - Load behavior with watch-enabled sources

4. **Environment Configuration**:
   - `from_env()` method
   - Environment variable configuration
   - Parameter overrides

## Test Files

### Core Tests

- `test_config.py` - Core Config class tests
- `test_config_validation.py` - Configuration validation tests
- `test_config_check_variables.py` - Variable checking and diagnostics
- `test_converters.py` - Type conversion tests
- `test_resolver.py` - Source resolution and merging tests
- `test_store.py` - ConfigStore tests
- `test_validators.py` - Validator tests
- `test_sources_*.py` - Individual source tests

### Integration Tests

- `test_sources_etcd_integration.py` - Etcd source integration tests (21 tests)
- `test_etcd_watch_integration.py` - Etcd watch and dynamic updates tests (14 tests)
- `test_etcd_connection.py` - Etcd connection verification script
- `test_integration.py` - General integration tests

### Tutorial Examples

- `test_tutorial_examples.py` - Tests for tutorial examples

## Test Markers

Tests are marked using pytest markers:

- `@pytest.mark.integration` - Integration tests requiring external services
- `@pytest.mark.etcd` - Tests requiring etcd
- `@pytest.mark.slow` - Slow-running tests

By default, integration tests are excluded. To run them:

```bash
pytest -m integration
```

## Continuous Integration

In CI environments:

1. **Unit tests only** (fast, no external dependencies):
   ```bash
   pytest tests/ -v -m "not integration"
   ```

2. **With etcd** (if etcd service is available):
   ```bash
   pytest tests/ -v -m etcd
   ```

3. **Full test suite** (requires all external services):
   ```bash
   pytest tests/ -v -m integration
   ```

## Writing Tests

### Test Structure

```python
import pytest
from varlord import Config
from varlord.sources import Env

def test_example():
    """Test description."""
    cfg = Config(
        model=AppConfig,
        sources=[Env()],
    )
    result = cfg.load()
    assert result.host == "expected"
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
def test_with_external_service():
    """Test that requires external service."""
    # Test implementation
    pass
```

### Etcd Test Example

```python
import pytest

@pytest.mark.etcd
@pytest.mark.integration
def test_etcd_source(etcd_client, etcd_cleanup):
    """Test etcd source functionality."""
    prefix = "/test/"
    etcd_cleanup(prefix)
    
    # Setup
    etcd_client.put(f"{prefix}host", "example.com")
    
    # Test
    source = Etcd.from_env(prefix=prefix)
    result = source.load()
    
    # Assert
    assert result["host"] == "example.com"
```

## Troubleshooting

### Tests Fail with Import Errors

Make sure all dependencies are installed:

```bash
make dev-install
# or
uv sync --all-extras --dev
```

### Etcd Connection Fails

1. Verify etcd is running:
   ```bash
   etcdctl endpoint health
   ```

2. Check certificate paths:
   ```bash
   ls -la ./cert/
   ```

3. Test connection manually:
   ```bash
   make test-etcd-connection
   ```

### Tests Timeout

Some integration tests may timeout if external services are slow. Increase timeout:

```bash
pytest tests/ --timeout=30
```

## Test Statistics

- **Total Tests**: 271+ tests
- **Unit Tests**: ~236 tests
- **Integration Tests**: ~35 tests (excluded by default)
- **Etcd Tests**: 35 tests (21 integration + 14 watch)

All tests should pass before submitting a pull request.

