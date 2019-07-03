Converters
==========

Converters are one of the core aspects of konfi. Converters make it possible to
provide full type-safety to templates.

You can add new converters by using the `konfi.register_converter`
decorator or simply passing the converter argument to `konfi.field`.

Converters should be stable i.e. if a value already has the correct type, the
converter should return the same value (not necessarily the same value by
identity, but by equality).


Builtin converters
------------------

.. currentmodule:: typing

+--------------------------+---------------------------------------------------+
| Type                     | Notes                                             |
+==========================+===================================================+
| `None` (NoneType)        | Always returns `None`.                            |
+--------------------------+---------------------------------------------------+
| `Any`                    | Returns the value directly.                       |
+--------------------------+---------------------------------------------------+
| - `bool`                 | Implemented by calling the type with the value.   |
| - `int`                  |                                                   |
| - `float`                |                                                   |
| - `complex`              |                                                   |
| - `bytes`                |                                                   |
| - `str`                  |                                                   |
+--------------------------+---------------------------------------------------+
| `Iterable`               | If the value is already iterable, it is returned  |
|                          | directly, unless it is a string. Everything else  |
|                          | is wrapped in a list and returned.                |
+--------------------------+---------------------------------------------------+
| - `tuple` (`Tuple`)      | Implemented by converting to an `Iterable` first  |
| - `list` (`List`)        | and then passing the result to the type.          |
| - `set` (`Set`)          |                                                   |
+--------------------------+---------------------------------------------------+
| `Mapping`                | If the value is already a `Mapping` it's returned |
|                          | directly.                                         |
|                          | If the value is a `Sequence` it is converted to a |
|                          | `dict` by using the index as the key and the item |
|                          | as the value.                                     |
|                          | All other value types raise a conversion error.   |
+--------------------------+---------------------------------------------------+
| `dict` (`Dict`)          | Implemented by converting to a `Mapping` and then |
|                          | passing the result to the type.                   |
+--------------------------+---------------------------------------------------+
| `Union`\[T1, T2]         | Returns value directly if it's already in the     |
|                          | union, otherwise returns the first successful     |
|                          | conversion result of trying each type from left   |
|                          | to right.                                         |
+--------------------------+---------------------------------------------------+
| `Tuple`\[T1, T2]         | For n-tuples (tuples with a limited amount of     |
|                          | items) each item is converted to the              |
|                          | corresponding type. This requires that the        |
|                          | lengths of the tuples are equal.                  |
|                          |                                                   |
|                          | Variadic tuples (tuples with an unspecified       |
|                          | amount of items) are handled by converting each   |
|                          | item to the value type.                           |
+--------------------------+---------------------------------------------------+
| `Iterable`\[T]           | Works for all subtypes like `List`\[T], `Set`\[T] |
|                          | and so on.                                        |
|                          | Implemented by gathering the items converted to T |
|                          | in a `list` and then converting that to the       |
|                          | container type.                                   |
+--------------------------+---------------------------------------------------+
| `Mapping`\[K, V]         | Works analogous to `Iterable`\[T].                |
+--------------------------+---------------------------------------------------+
| `enum.Enum`              | Tries to find the appropriate member in the       |
|                          | following order:                                  |
|                          |                                                   |
|                          | 1. Perfect name match                             |
|                          | 2. Perfect value match                            |
|                          | 3. First case-insensitive match on either name or |
|                          |    value                                          |
+--------------------------+---------------------------------------------------+
