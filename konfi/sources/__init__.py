"""Sources contains konfi's built-in sources."""

from .env import Env
from .file import FileLoader, has_file_loader, register_file_loader

# TODO use dummy loaders which raise when they're being used

try:
    from .toml import TOML
except ImportError:
    pass

try:
    from .yaml import YAML
except ImportError:
    pass
