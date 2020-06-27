# This file is part of sunflower package. radio
# Mixins

from collections import namedtuple
from typing import Iterable, Optional, Type

from sunflower.core.descriptors import PersistentAttribute


class ProvideViewMixin:
    """Provide access to a view object containing values of persistent attributes only."""
    data_type: str = ""
    __proxy_tuple = namedtuple("ObjectProxy", ["data_type", "endpoint"])
    __view_tuple: Optional[Type[namedtuple]] = None
    __persistent_attributes = ()

    @classmethod
    def get_view(cls, endpoint):
        if cls.data_type == "":
            raise TypeError("This class must have a nonempty data_type str attribute")
        if cls.__view_tuple is None:
            persistent_attributes = []
            for name, value in cls.__dict__.items():
                if isinstance(value, PersistentAttribute):
                    persistent_attributes.append(name)
            cls.__persistent_attributes = tuple(persistent_attributes)
            cls.__view_tuple = namedtuple(cls.__name__ + "View", cls.__persistent_attributes + cls.__proxy_tuple._fields)
        object_proxy = cls.__proxy_tuple(cls.data_type, endpoint)
        return cls.__view_tuple._make(
            tuple(getattr(cls, name).__get__(object_proxy, cls) for name in cls.__persistent_attributes)
            + tuple(getattr(object_proxy, name) for name in cls.__proxy_tuple._fields)
        )


class HTMLMixin:
    """Provide static mixin methods for formatting html elements."""

    @staticmethod
    def _format_html_anchor_element(href: str, text: str, classes: Iterable[str] = ()) -> str:
        """Generate html code for anchor tag.

        Parameters:
        - href (str)
        - text of the link (str)
        - a list of classes for this element (list(str))

        If bool(href) == False (i.e. href is None or empty string), return text only
        """
        if not href:
            return text
        classes_str = " ".join(classes)
        return f'<a target="_blank" class="{classes_str}" href="{href}">{text}</a>'
