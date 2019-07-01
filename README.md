# konfi

[![CircleCI](https://circleci.com/gh/gieseladev/konfi.svg?style=svg)](https://circleci.com/gh/gieseladev/konfi)
[![Documentation Status](https://readthedocs.org/projects/konfi/badge/?version=latest)](https://konfi.readthedocs.io/en/latest/?badge=latest)

Cute config parser.


## Example

```python
from typing import Optional

import konfi


@konfi.template()
class UserInfo:
    name: str
    country: Optional[str]


@konfi.template()
class AppConfig:
    name: str = "konfi"
    user: UserInfo


konfi.set_sources(
    konfi.YAML("config.yml", ignore_not_found=True),
    konfi.Env(prefix="app_"),
)

config = konfi.load(AppConfig)

greeting = f"Hello {config.user.name}"
if config.user.country:
    greeting += f" from {config.user.country}"
    
print(greeting)
print(f"Welcome to {config.name}!")
```