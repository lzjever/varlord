# Development Setup

## Quick Start

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Set up the project**:
   
   **Recommended: For active development**
   ```bash
   make dev-install
   ```
   This installs the package and all dependencies. Use this for normal development.
   
   **Alternative: Dependencies only (for CI/CD or tools)**
   ```bash
   make setup-venv
   ```
   This only installs dependencies, not the package. Useful for CI/CD or when you only need tools.

3. **Run tests**:
   ```bash
   make test
   ```

That's it! The Makefile automatically uses `uv` if available, otherwise falls back to `pip`.

## What Changed from Conda?

- ✅ **Faster**: uv is 10-100x faster than pip/conda
- ✅ **Simpler**: One tool for virtualenv, pip, and dependency management
- ✅ **Reproducible**: `uv.lock` ensures consistent builds
- ✅ **Compatible**: Works with existing `pyproject.toml`

## Common Commands

```bash
make dev-install    # Install all dependencies
make test           # Run tests
make lint           # Run linting
make format         # Format code
make docs           # Build documentation
make check          # Run all checks
```

For more details, see [UV_SETUP.md](UV_SETUP.md).
