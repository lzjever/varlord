# UV Setup Guide

This project uses [uv](https://github.com/astral-sh/uv) for fast and reliable dependency management.

## What is uv?

`uv` is an extremely fast Python package installer and resolver written in Rust. It's designed to be a drop-in replacement for `pip`, `pip-tools`, `virtualenv`, and `pipx`.

## Installation

### Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or on Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installation, add `~/.local/bin` to your PATH (or restart your terminal).

### Verify Installation

```bash
uv --version
```

## Quick Start

### Initial Setup

**Option 1: Setup virtual environment only (recommended for fresh checkout)**

```bash
# Create virtual environment and install dependencies (without installing the package)
make setup-venv

# Later, if you want to install the package:
make install
```

**Option 2: Setup and install package (for development)**

```bash
# Install all dependencies (including dev and docs groups) AND install the package
make dev-install

# Or manually (dev group is installed by default)
uv sync --group docs --all-extras
```

This will:
- Create a virtual environment in `.venv/`
- Install all dependencies from `pyproject.toml`
- Generate `uv.lock` for reproducible builds

### Common Commands

```bash
# Run tests
make test
# Or: uv run pytest tests/ -v

# Run linting
make lint
# Or: uv run flake8 varlord/ tests/

# Format code
make format
# Or: uv run black varlord/ tests/

# Build documentation
make docs
# Or: uv run python -m sphinx docs/source docs/build/html

# Run any Python command
uv run python script.py

# Add a new dependency
uv add package-name

# Add a dev dependency (to dev group)
uv add --group dev package-name

# Add a dependency to docs group
uv add --group docs package-name

# Add an optional runtime dependency (extra)
uv add --optional etcd package-name

# Remove a dependency
uv remove package-name

# Update dependencies
uv sync --upgrade
```

## Understanding Dependency Groups vs Extras

This project uses two types of optional dependencies:

### Dependency Groups (PEP 735)
- **`dev`**: Development dependencies (pytest, black, flake8, etc.) - **installed by default** with `uv sync`
- **`docs`**: Documentation dependencies (sphinx, themes, etc.) - install with `--group docs`

Dependency groups are **not published to PyPI** and are only for local development.

### Extras (Optional Runtime Features)
- **`dotenv`**: Support for `.env` files - install with `--extra dotenv` or `--all-extras`
- **`etcd`**: Support for etcd configuration source - install with `--extra etcd` or `--all-extras`

Extras are **published to PyPI** and can be installed by end users.

### Common Commands

```bash
# Install with dev group (default) + all extras
uv sync --all-extras

# Install with dev + docs groups + all extras
uv sync --group docs --all-extras

# Install only runtime dependencies (no groups, no extras)
uv sync

# Install with specific extra
uv sync --extra etcd
```

## How It Works

1. **Virtual Environment**: uv automatically creates and manages `.venv/` in your project root
2. **Lock File**: `uv.lock` ensures reproducible builds across different machines
3. **Fast**: uv is 10-100x faster than pip for dependency resolution
4. **Compatible**: Works with existing `pyproject.toml` and `setup.py` projects
5. **Project-Based**: Uses `uv.lock` for reproducible builds (like Poetry/PDM)

## Makefile Integration

The Makefile automatically detects if `uv` is available:

- If `uv` is found: Uses `uv run` for all Python commands
- If `uv` is not found: Falls back to `pip` and `python`

This means the Makefile works with or without uv installed.

## Migration from Conda

If you're migrating from conda:

1. **Remove conda environment**:
   ```bash
   conda deactivate
   conda env remove -n your-env-name
   ```

2. **Install uv** (see above)

3. **Set up project**:
   ```bash
   make dev-install
   ```

4. **Activate virtual environment** (if needed):
   ```bash
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate  # Windows
   ```

5. **Update your shell profile** (optional):
   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   export PATH="$HOME/.local/bin:$PATH"
   ```

## Benefits

- ⚡ **Fast**: 10-100x faster than pip
- 🔒 **Reproducible**: Lock file ensures consistent builds
- 🎯 **Simple**: One tool for virtualenv, pip, and pip-tools
- 🔄 **Compatible**: Works with existing Python projects
- 📦 **Modern**: Built for modern Python packaging standards

## Troubleshooting

### uv command not found

Make sure `~/.local/bin` is in your PATH:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Virtual environment issues

Clear and recreate:
```bash
rm -rf .venv
uv sync --group docs --all-extras
```

### Lock file conflicts

Regenerate the lock file:
```bash
rm uv.lock
uv lock
uv sync --group docs --all-extras
```

## More Information

- [uv Documentation](https://docs.astral.sh/uv/)
- [uv GitHub](https://github.com/astral-sh/uv)

