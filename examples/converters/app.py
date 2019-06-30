from typing import Any, Tuple

from models import Location, Temperature

import konfi


# let's tell konfi how to convert to a Location

@konfi.register_converter(Location)
def location_converter(value: Any) -> Location:
    # this works! If you're not amazed by this then I don't know what's wrong
    # with you
    lat, long = konfi.convert_value(value, Tuple[float, float])
    return Location(lat, long)


@konfi.template()
class Config:
    loc: Location
    # you can also pass a one-time converter instead of registering a new one.
    temp: Temperature = konfi.field(converter=Temperature.create)


if __name__ == "__main__":
    konfi.set_sources(
        konfi.FileLoader("config.toml", ignore_not_found=True),
    )

    config = konfi.load(Config)

    print(f"it's {config.temp} at {config.loc}")
