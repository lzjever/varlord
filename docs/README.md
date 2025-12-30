# Varlord Documentation

This directory contains the Sphinx documentation for Varlord.

## Building Documentation

```bash
cd docs
make html
```

The generated HTML will be in `docs/build/html/`.

## Documentation Structure

- `source/introduction.rst` - Introduction and overview
- `source/design.rst` - System design and architecture
- `source/quickstart.rst` - Quick start guide
- `source/user_guide/` - Comprehensive user guide
- `source/api_reference/` - Complete API documentation
- `source/examples/` - Usage examples

## Requirements

Install documentation dependencies:

```bash
pip install -e ".[docs]"
```

