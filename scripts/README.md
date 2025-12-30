# Scripts

This directory contains utility scripts for development and release management.

## generate_release_notes.py

Generates release notes from CHANGELOG.md or git commits for a specific version.

### Usage

```bash
python3 scripts/generate_release_notes.py <version> [output_file]
```

If `output_file` is not provided, output goes to stdout.

### Examples

```bash
# Output to stdout
python3 scripts/generate_release_notes.py 0.1.0

# Output to file
python3 scripts/generate_release_notes.py 0.1.0 release_notes.md
```

### Description

This script extracts the release notes for a specific version from `CHANGELOG.md`.
It looks for sections matching the pattern `## [<version>]` and extracts
the content until the next version section.

If the version is not found in CHANGELOG.md, it falls back to extracting
git commits since the previous tag.

The script also automatically adds installation instructions to the release notes.

