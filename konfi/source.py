import abc
import dataclasses
import functools
from typing import Any, Dict, Iterable, Iterator, List, Mapping

import konfi

__all__ = ["SourceABC", "QualifiedField", "iter_fields_recursively",
           "load_field_value", "load_fields_values"]


class SourceABC(abc.ABC):
    @abc.abstractmethod
    def load_into(self, obj: Any, template: type) -> None:
        ...


@dataclasses.dataclass()
class QualifiedField:
    parent: Any
    path: List[str]
    field: konfi.Field


def iter_fields_recursively(obj: Any, template: Any) -> Iterator[QualifiedField]:
    def iter_fields(parent: Any, path: List[str], fields: Iterable[konfi.Field]) -> None:
        for field in fields:
            key_path = [*path, field.key]

            if konfi.is_template_like(field.value_type):
                sub_obj = _get_sub_obj(obj, field)
                yield from iter_fields(sub_obj, key_path, konfi.fields(field.value_type))
            else:
                yield QualifiedField(parent, key_path, field)

    yield from iter_fields(obj, [], konfi.fields(template))


def load_field_value(obj: Any, field: konfi.Field, value: Any) -> None:
    try:
        converted = konfi.convert_value(value, field.value_type)
    except Exception:
        # TODO only catch conversion exception
        # TODO raise
        raise

    setattr(obj, field.attribute, converted)


def _get_sub_obj(obj: Any, field: konfi.Field) -> Any:
    try:
        value = getattr(obj, field.attribute)
    except AttributeError:
        value = object.__new__(field.value_type)
        setattr(obj, field.attribute, value)

    return value


def load_fields_values(obj: Any, fields: Iterable[konfi.Field], mapping: Mapping, *,
                       ignore_unknown: bool = False) -> None:
    _field_by_keys: Dict[str, konfi.Field] = {field.key: field for field in fields}

    for key, value in mapping.items():
        try:
            field = _field_by_keys[key]
        except KeyError:
            if ignore_unknown:
                continue
            else:
                # TODO raise something
                raise Exception

        if konfi.is_template_like(field.value_type) and isinstance(value, Mapping):
            sub_obj = _get_sub_obj(obj, field)
            loader = functools.partial(load_fields_values, sub_obj, konfi.fields(sub_obj), value)
        else:
            loader = functools.partial(load_field_value, obj, field, value)

        try:
            loader()
        except Exception:
            # TODO add more detail
            raise
