from typing import Any, Callable, Optional, Type, TypeVar

from . import typeinspect
from .converter import ConverterType

__all__ = ["ValueFactory", "MISSING", "UnboundField", "Field", "upgrade_unbound", "field"]

FT = TypeVar("FT")
ValueFactory = Callable[[], Any]

MISSING = object()


class NoDefaultValue(Exception):
    ...


class UnboundField:
    key: Optional[str]
    comment: Optional[str]

    default_value: Any
    default_factory: Optional[ValueFactory]

    converter: ConverterType

    # TODO ability to specify converter manually

    def __init__(self, *,
                 key: str = None,
                 comment: str = None,
                 default_value: Any = MISSING,
                 default_factory: ValueFactory = None,
                 converter: ConverterType = None,
                 ) -> None:
        self.key = key
        self.comment = comment

        if default_value is not MISSING and default_factory is not None:
            raise ValueError("can't specify both default factory and value!")

        self.default_value = default_value
        self.default_factory = default_factory

        self.converter = converter

    @property
    def required(self) -> bool:
        return self.default_value is MISSING and self.default_factory is None

    def get_default(self) -> Any:
        if self.default_value is not MISSING:
            return self.default_value
        elif self.default_factory is not None:
            return self.default_factory()
        else:
            raise NoDefaultValue


class Field(UnboundField):
    attribute: str
    key: str

    value_type: Type

    def __init__(self, *,
                 attribute: str,
                 key: str = None,
                 comment: str = None,
                 value_type: Type,
                 default_value: Any = MISSING,
                 default_factory: ValueFactory = None,
                 converter: ConverterType = None,
                 ) -> None:
        if key is None:
            key = attribute

        super().__init__(key=key, comment=comment,
                         default_value=default_value, default_factory=default_factory,
                         converter=converter)
        self.attribute = attribute
        self.value_type = value_type

    @property
    def optional_type(self) -> bool:
        return typeinspect.is_optional(self.value_type)

    @property
    def required(self) -> bool:
        return super().required and not self.optional_type

    def get_default(self) -> Any:
        try:
            return super().get_default()
        except NoDefaultValue as e:
            if self.optional_type:
                return None
            else:
                raise e


def upgrade_unbound(unbound: UnboundField, *, attribute: str, value_type: Type) -> Field:
    return Field(
        attribute=attribute,
        key=unbound.key,
        comment=unbound.comment,
        value_type=value_type,
        default_value=unbound.default_value,
        default_factory=unbound.default_factory,
        converter=unbound.converter,
    )


def field(*, key: str = None, comment: str = None,
          default: Any = MISSING, factory: ValueFactory = None,
          converter: ConverterType = None,
          ) -> UnboundField:
    return UnboundField(
        key=key,
        comment=comment,
        default_value=default,
        default_factory=factory,
        converter=converter,
    )
