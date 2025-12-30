"""
Configuration sources module.

Provides various configuration sources:
- Defaults: From dataclass model defaults
- DotEnv: From .env files
- Env: From environment variables
- CLI: From command-line arguments
- Etcd: From etcd (optional, requires etcd extra)
"""

from varlord.sources.base import Source, ChangeEvent
from varlord.sources.defaults import Defaults
from varlord.sources.env import Env
from varlord.sources.cli import CLI

__all__ = [
    "Source",
    "ChangeEvent",
    "Defaults",
    "Env",
    "CLI",
]

# Optional sources (require extras)
try:
    from varlord.sources.dotenv import DotEnv

    __all__.append("DotEnv")
except ImportError:
    pass

try:
    from varlord.sources.etcd import Etcd

    __all__.append("Etcd")
except ImportError:
    pass
