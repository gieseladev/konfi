# konfi

[![CircleCI](https://circleci.com/gh/gieseladev/konfi.svg?style=svg)](https://circleci.com/gh/gieseladev/konfi)
[![Documentation Status](https://readthedocs.org/projects/konfi/badge/?version=latest)](https://konfi.giesela.dev/en/latest/?badge=latest)

Cute config parser.
You know I really tried to come up with a catchy one-liner there, but 
It goes without saying that I failed miserably.

Anyway, konfi lets you create config templates similar to 
[dataclasses](https://docs.python.org/3/library/dataclasses.html). 
These templates are then used to load the config from different sources.
Konfi guarantees that the loaded config corresponds to the template even
going as far as making sure items of a list are of the right type.

This means you no longer have to worry about the validity of the config,
if the config is correct it will load and if it isn't it will raise an
error telling you why not.


## Installation

You can install konfi from [PyPI](https://pypi.org/project/konfi/):

```bash
pip install konfi
```


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

For more examples see the [examples/](examples) directory.


## Documentation

If you're ready to jump in, you can find the documentation on 
[Read the Docs](https://konfi.giesela.dev).