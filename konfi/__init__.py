"""konfi is a config parser."""

from .converter import ComplexConverterABC, ConversionError, ConverterABC, \
    ConverterFunc, ConverterType, convert_value, has_converter, \
    register_converter, unregister_converter
from .field import Field, MISSING, NoDefaultValue, UnboundField, ValueFactory, field
from .loader import Loader, SourceError
from .source import FieldError, MultiPathError, PathError, SourceABC
from .sources import *
from .templ import create_object_from_template, fields, get_field, is_template, is_template_like, template

# load built-in converters
from . import converters

__version__ = "0.2.1"
__author__ = "Giesela Inc."

default_loader = Loader()
set_sources = default_loader.set_sources
load = default_loader.load
