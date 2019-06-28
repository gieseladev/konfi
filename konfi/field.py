from typing import Any, Callable, Optional, Type, TypeVar

__all__ = ["ValueFactory", "UnboundField", "Field", "upgrade_unbound", "field"]

FT = TypeVar("FT")
ValueFactory = Callable[[], Any]

_MISSING = object()


class UnboundField:
    key: Optional[str]
    comment: Optional[str]

    default_value: Any
    default_factory: Optional[ValueFactory]

    # TODO ability to specify converter manually

    def __init__(self, *,
                 key: str = None,
                 comment: str = None,
                 default_value: Any = _MISSING,
                 default_factory: ValueFactory = None,
                 ) -> None:
        self.key = key
        self.comment = comment

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
    config_key: str
    description: Optional[str]

    value_type: Type
    default_value: Any

    def __init__(self, *,
                 attribute: str,
                 key: str = None,
                 comment: str = None,
                 value_type: Type,
                 default_value: Any = _MISSING,
                 default_factory: ValueFactory = None,
                 ) -> None:
        super().__init__(key=key, comment=comment,
                         default_value=default_value, default_factory=default_factory)
        self.attribute = attribute
        self.value_type = value_type


def upgrade_unbound(unbound: UnboundField, *, attribute: str, value_type: Type) -> Field:
    return Field(
        attribute=attribute,
        key=unbound.key,
        comment=unbound.comment,
        value_type=value_type,
        default_value=unbound.default_value,
        default_factory=unbound.default_factory,
    )


def field(*, key: str = None, comment: str = None,
          default: Any = _MISSING, factory: ValueFactory = None,
          ) -> UnboundField:
    return UnboundField(
        key=key,
        comment=comment,
        default_value=default,
        default_factory=factory,
    )
