# This file is part of sunflower package. radio
# Mixins

from typing import Iterable


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
