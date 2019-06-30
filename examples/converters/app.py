import re
from typing import Any, Tuple

import konfi


# our beautiful and useless data structure for storing a location:

class Location:
    latitude: float
    longitude: float

    def __init__(self, lat: float, long: float) -> None:
        self.latitude = lat
        self.longitude = long

    def __str__(self) -> str:
        return f"({self.latitude}, {self.longitude})"


# let's tell konfi how to convert to this type

@konfi.register_converter(Location)
def location_converter(value: Any) -> Location:
    # this works! If you're not amazed by this then I don't know what's wrong
    # with you
    lat, long = konfi.convert_value(value, Tuple[float, float])
    return Location(lat, long)


# let's also define a nice temperature data structure

class Temperature:
    _kelvin: float

    def __init__(self, kelvin: float = 0) -> None:
        self.kelvin = kelvin

    def __str__(self) -> str:
        return f"{self.degrees:.2} °C"

    @property
    def kelvin(self) -> float:
        return self._kelvin

    @kelvin.setter
    def kelvin(self, value: float) -> None:
        if value < 0:
            raise ValueError("Temperature cannot be less than 0 Kelvin")

        self._kelvin = value

    @property
    def degrees(self) -> float:
        return self.kelvin - 273.15

    @degrees.setter
    def degrees(self, value: float) -> None:
        self.kelvin = value + 273.15

    @property
    def stupid(self) -> float:
        return self.degrees * 1.8 + 32

    @stupid.setter
    def stupid(self, value: float) -> None:
        self.degrees = (value - 32) / 1.8

    @classmethod
    def create(cls, value: Any):
        inst = cls()

        if isinstance(value, str):
            # mad regex
            match = re.match(r"(\d+[.\d]*)\s?(°c|°f|k)", value, re.IGNORECASE)
            if match is None:
                raise ValueError(f"Invalid temperature: {value!r}")
            temp_str, symbol = match.groups()
            temp = float(temp_str)

            # poor man's switch
            if symbol == "k":
                inst.kelvin = temp
            elif symbol == "c":
                inst.degrees = temp
            else:
                inst.stupid = temp

        elif isinstance(value, (float, int)):
            # yes, unitless numbers are de facto celsius, fight me
            inst.degrees = value
        else:
            raise TypeError("Invalid value type for temperature")

        return inst


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
