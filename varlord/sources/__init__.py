"""
Configuration sources module.

Provides various configuration sources:
- Defaults: From dataclass model defaults
- DotEnv: From .env files
- Env: From environment variables
- CLI: From command-line arguments
- Etcd: From ``etcd`` key-value store (optional, requires ``etcd`` extra)

Note: The Etcd source requires the ``etcd`` extra to be installed.
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

# Optional sources (require extras)
try:
    from varlord.sources.dotenv import DotEnv  # noqa: F401

    __all__.append("DotEnv")
except ImportError:
    pass

try:
    from varlord.sources.etcd import Etcd  # noqa: F401

    __all__.append("Etcd")
except ImportError:
    pass
