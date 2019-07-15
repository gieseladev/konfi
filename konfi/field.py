from typing import Any, Callable, Optional, TYPE_CHECKING, Type, TypeVar

from . import typeinspect
from .converter import ConverterType

__all__ = ["ValueFactory", "MISSING",
           "NoDefaultValue",
           "UnboundField", "Field",
           "upgrade_unbound", "field"]

FT = TypeVar("FT")
ValueFactory = Callable[[], Any]
ValueFactory.__doc__ = \
    """Callable which when called, returns a value."""

# only use "expensive" sentinel for documentation
if TYPE_CHECKING:
    class MISSING:
        """Sentinel representing a missing value.

        This is used to represent the lack of a default value, because
        `None` would lead to a conflict.
        """

        def __repr__(self) -> str:
            return "MISSING"


    MISSING = MISSING()
else:
    MISSING = object()


class NoDefaultValue(Exception):
    """Exception for when a default value is expected, but doesn't exist."""
    ...


class UnboundField:
    """A field that hasn't been bound to a template.

    Note that an unbound field is usually created using the `field`
    function, not directly.

    Attributes:
        key (Optional[str]): Corresponding config key to use.
        comment (Optional[str]): Comment for the field.
        default_value (Any): The default value of the field.
            The value `MISSING` is used if no default value exists.
        default_factory (Optional[ValueFactory]): Factory to call to
            get the default value.
        converter (Optional[ConverterType]): Converter to use.

    Raises:
        ValueError: If both factory and default value are specified.
    """
    key: Optional[str]
    comment: Optional[str]

    default_value: Any
    default_factory: Optional[ValueFactory]

    converter: Optional[ConverterType]

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

    def __repr__(self) -> str:
        return f"UnboundField(key={self.key!r}, comment={self.comment!r})"

    @property
    def required(self) -> bool:
        """Checks whether the field must be set."""
        return self.default_value is MISSING and self.default_factory is None

    def get_default(self) -> Any:
        """Get the default value of the field.

        This uses either the default value or calls the default factory.

        Raises:
            NoDefaultValue: If the field doesn't have a default value.
        """
        if self.default_value is not MISSING:
            return self.default_value
        elif self.default_factory is not None:
            return self.default_factory()
        else:
            raise NoDefaultValue


class Field(UnboundField):
    """A field of a template.

    Field is a superset of `UnboundField` meaning it inherits all attributes
    and arguments.

    Attributes:
        attribute (str): Name of the attribute the field belongs to.
        key (str): Name of the config key.
        value_type (Type): Expected type of the field.
    """
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

    def __repr__(self) -> str:
        return f"Field(attribute={self.attribute!r}, value_type={self.value_type!r}, key={self.key!r}, comment={self.comment!r})"

    def __str__(self) -> str:
        key_str = f" [{self.key!r}]" if self.key != self.attribute else ""
        return f"Field({self.attribute}{key_str})"

    @property
    def optional_type(self) -> bool:
        """Whether the value type is optional (ex: Optional[str])."""
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
    """Upgrade an unbound field to a field.

    Args:
        unbound: Unbound field to upgrade.
        attribute: Attribute name of the field.
        value_type: Value type of the field.

    Returns:
        A field with the values of the unbound field.
    """
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
    """Specify a field options.

    This creates an unbound field which is later upgraded to a bound field when
    the template is created. The class variable is also replaced with the
    default value of the field and if no default value exists, it is removed.

    Args:
        key: Config key to use (instead of the attribute name).
        comment: Comment for the field.
        default: Default value for the field.
        factory: Factory method to use to get the default value.
            You can't set both the default and the factory value.
        converter: Custom converter to use.

    Raises:
        ValueError: If both factory and default value are specified.

    Returns:
        An unbound field.
    """
    return UnboundField(
        key=key,
        comment=comment,
        default_value=default,
        default_factory=factory,
        converter=converter,
    )
