.. currentmodule:: konfi

API Reference
=============


Template
--------

.. autodecorator:: template

.. autofunction:: is_template

.. autofunction:: is_template_like

.. autofunction:: fields

.. autofunction:: get_field


Field
-----

.. autofunction:: field

.. autoclass:: UnboundField
    :members:

.. autoclass:: Field
    :members:

.. autodata:: ValueFactory

.. autodata:: MISSING


Loader
------

.. autofunction:: set_sources

.. autofunction:: load

.. autoclass:: Loader
    :members:


Source
------

.. autoclass:: SourceABC
    :members:

.. autodecorator:: register_file_loader

.. autofunction:: has_file_loader

.. autoclass:: FileLoader

.. autoclass:: Env

.. autoclass:: TOML

.. autoclass:: YAML


Converter
---------

.. autofunction:: convert_value

.. autofunction:: has_converter

.. autodecorator:: register_converter

.. autofunction:: unregister_converter

.. autodata:: ConverterType

.. autodata:: ConverterFunc

.. autoclass:: ConverterABC
    :members:

.. autoclass:: ComplexConverterABC
    :show-inheritance:
    :members:


Exceptions
----------

.. autoexception:: SourceError
    :show-inheritance:
    :members:

.. autoexception:: PathError
    :show-inheritance:
    :members:

.. autoexception:: FieldError
    :show-inheritance:
    :members:

.. autoexception:: MultiPathError
    :show-inheritance:
    :members:

.. autoexception:: NoDefaultValue
    :show-inheritance:
    :members:

.. autoexception:: ConversionError
    :show-inheritance:
    :members:
