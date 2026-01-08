"""
Configuration sources module.

Provides various configuration sources:
- Defaults: From dataclass model defaults
- DotEnv: From .env files
- Env: From environment variables
- CLI: From command-line arguments
- YAML: From YAML files (optional, requires ``yaml`` extra)
- JSON: From JSON files (standard library, no extra required)
- TOML: From TOML files (optional, requires ``toml`` extra for Python < 3.11)
- Etcd: From ``etcd`` key-value store (optional, requires ``etcd`` extra)

Note: Optional sources require their respective extras to be installed.
"""

from varlord.sources.base import ChangeEvent, Source
from varlord.sources.cli import CLI
from varlord.sources.defaults import Defaults
from varlord.sources.env import Env

__all__ = [
    "Source",
    "ChangeEvent",
    "Defaults",
    "Env",
    "CLI",
]

# JSON source (standard library, always available)
try:
    from varlord.sources.json import JSON  # noqa: F401

    __all__.append("JSON")
except ImportError:
    pass

# Optional sources (require extras)
try:
    from varlord.sources.dotenv import DotEnv  # noqa: F401

    __all__.append("DotEnv")
except ImportError:
    pass

try:
    from varlord.sources.yaml import YAML  # noqa: F401

    __all__.append("YAML")
except ImportError:
    pass

try:
    from varlord.sources.toml import TOML  # noqa: F401

    __all__.append("TOML")
except ImportError:
    pass

try:
    from varlord.sources.etcd import Etcd  # noqa: F401

    __all__.append("Etcd")
except (ImportError, TypeError):
    # TypeError can occur if etcd3 is installed but protobuf version is incompatible
    # In this case, treat etcd as unavailable
    pass
