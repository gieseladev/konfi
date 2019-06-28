from typing import Any, Callable, Optional, Type, TypeVar

__all__ = ["ValueFactory", "UnboundField", "Field", "upgrade_unbound", "field"]

FT = TypeVar("FT")
ValueFactory = Callable[[], Any]

_MISSING = object()


class UnboundField:
    name: Optional[str]
    description: Optional[str]

    default_value: Any
    default_factory: Optional[ValueFactory]

    # TODO ability to specify register_converter manually

    def __init__(self, *,
                 name: str = None,
                 description: str = None,
                 default_value: Any = _MISSING,
                 default_factory: ValueFactory = None,
                 ) -> None:
        self.name = name
        self.description = description

        if not (default_value is _MISSING and default_factory is None):
            raise ValueError("can't specify both default factory and value!")

        self.default_value = default_value
        self.default_factory = default_factory

    def has_default(self) -> bool:
        return self.default_value is not _MISSING or self.default_factory is not None

    def get_default(self) -> Any:
        if self.default_value is not _MISSING:
            return self.default_value
        elif self.default_factory is not None:
            return self.default_factory()
        else:
            return _MISSING


class Field(UnboundField):
    attribute: str
    name: str
    description: Optional[str]

    value_type: Type
    default_value: Any

    def __init__(self, *,
                 attribute: str,
                 name: str = None,
                 description: str = None,
                 value_type: Type,
                 default_value: Any = _MISSING,
                 default_factory: ValueFactory = None,
                 ) -> None:
        super().__init__(name=name, description=description,
                         default_value=default_value, default_factory=default_factory)
        self.attribute = attribute
        self.value_type = value_type


def upgrade_unbound(unbound: UnboundField, *, attribute: str, value_type: Type) -> Field:
    return Field(
        attribute=attribute,
        name=unbound.name,
        description=unbound.description,
        value_type=value_type,
        default_value=unbound.default_value,
        default_factory=unbound.default_factory,
    )


def field(*, name: str = None, desc: str = None,
          default: Any = _MISSING, factory: ValueFactory = None,
          ) -> UnboundField:
    return UnboundField(
        name=name,
        description=desc,
        default_value=default,
        default_factory=factory,
    )
