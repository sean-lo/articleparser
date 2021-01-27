"""Utility functions for other files.

Written January 2021.
"""

# Python 3.7 onwards, for annotations with standard collections
from __future__ import annotations

import itertools
import tempfile
import logging
from pathlib import Path
from typing import Any, Union, IO, AnyStr
import re

import bs4
import dateutil.parser
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError


LOGGER = logging.getLogger(__name__)


def make_soup(
    f: Union[AnyStr, Path, IO],
    parser: str = None,
) -> bs4.BeautifulSoup:
    """Make soup object.

    Parameters
    ----------
    f: AnyStr or Path or IO
        filepath pointing to HTML file.
    parser: {"html.parser", "lxml", "html5lib"}
        see https://www.crummy.com/software/BeautifulSoup/bs4/doc/#differences-between-parsers

    Returns
    -------
    soup : bs4.BeautifulSoup
        The HTML document.

    Raises
    ------
    ValueError
        if `f` is of type `AnyStr` or `Path` and does not end with ".html".
    ValueError
        if `parser` is not from the allowed list.
    FileNotFoundError
        if a filepath is provided but no file exists at that filepath.
    TypeError
        if `f` is not of type `AnyStr`, `Path`, or `IO`.
    """
    if parser is not None:
        if parser not in ["html.parser", "lxml", "html5lib"]:
            raise ValueError("Wrong parser format specified.")

    if isinstance(f, (str, bytes, Path)):
        filepath = str(f)
        if not filepath.endswith(".html"):
            LOGGER.error("filepath {} of wrong suffix".format(filepath))
            raise ValueError("filepath {} of wrong suffix".format(filepath))
        try:
            with open(str(filepath), "r", encoding="utf-8") as f:
                html_doc = f.read()
        except FileNotFoundError:
            LOGGER.error("No such file: {}".format(str(filepath)))
            raise FileNotFoundError
    elif isinstance(f, tempfile.SpooledTemporaryFile):
        html_doc = f.read()
        html_doc = str(html_doc, "utf-8")
    else:
        LOGGER.error("Wrong input type: {}".format(type(f)))
        raise TypeError("Wrong input type: {}".format(type(f)))

    # <iframe> tags in <head> have to be removed via regex
    # this is because parsers (even the lxml parser) will interpret <iframe>
    # tags in <head> to be belonging to <body>, and begin <body> prematurely
    html_doc = remove_iframes_in_head(html_doc)
    # similarly, while <noscript> tags in <head> are legal,
    # <noscript> tags can contain flow content when in <body> but not in <head>;
    # easier to just remove all of these (especially in the head)
    html_doc = remove_noscripts_in_head(html_doc)
    # html_doc = remove_scripts_in_head(html_doc)

    if parser:
        soup = bs4.BeautifulSoup(html_doc, parser)
    else:
        soup = bs4.BeautifulSoup(html_doc, "html5lib")
    return soup


def remove_iframes_in_head(html_doc: str) -> str:
    IFRAME_IN_HEAD_REGEX = re.compile(
        r"""
            (?P<before>                 # "before" capturing group, 
                <head(?:\s[^>]+)?>          # "<head ...>" or "<head>"
                (?:.*?)                     # non-capturing, 0 or more chars
            )
            (                           # "iframe" capturing group
                <iframe[^>]*                # "<iframe..."
                (?:\/>|>.*?<\/iframe>)      # "/>" or ">...</iframe>"
            )
            (?P<after>                  # "after" capturing group
                (?:.*?)                     # non-capturing, 0 or more chars
                <\/head>                    # "</head>"
            )
        """,
        flags=re.VERBOSE | re.DOTALL,
    )
    while True:
        new_html_doc = re.sub(IFRAME_IN_HEAD_REGEX, r"\g<before>\g<after>", html_doc)
        if new_html_doc == html_doc:
            return new_html_doc
        html_doc = new_html_doc


def remove_noscripts_in_head(html_doc: str) -> str:
    NOSCRIPT_IN_HEAD_REGEX = re.compile(
        r"""
            (?P<before>                 # "before" capturing group, 
                <head(?:\s[^>]+)?>          # "<head ...>" or "<head>"
                (?:.*?)                     # non-capturing, 0 or more chars
            )
            (                           # "iframe" capturing group
                <noscript[^>]*                # "<iframe..."
                (?:\/>|>.*?<\/noscript>)      # "/>" or ">...</iframe>"
            )
            (?P<after>                  # "after" capturing group
                (?:.*?)                     # non-capturing, 0 or more chars
                <\/head>                    # "</head>"
            )
        """,
        flags=re.VERBOSE | re.DOTALL,
    )

    while True:
        new_html_doc = re.sub(NOSCRIPT_IN_HEAD_REGEX, r"\g<before>\g<after>", html_doc)
        if new_html_doc == html_doc:
            return new_html_doc
        html_doc = new_html_doc


def remove_scripts_in_head(html_doc: str) -> str:
    SCRIPT_IN_HEAD_REGEX = re.compile(
        r"""
            (?P<before>                 # "before" capturing group, 
                <head(?:\s[^>]+)?>          # "<head ...>" or "<head>"
                (?:.*?)                     # non-capturing, 0 or more chars
            )
            (                           # "iframe" capturing group
                <script[^>]*                # "<iframe..."
                (?:\/>|>.*?<\/script>)      # "/>" or ">...</iframe>"
            )
            (?P<after>                  # "after" capturing group
                (?:.*?)                     # non-capturing, 0 or more chars
                <\/head>                    # "</head>"
            )
        """,
        flags=re.VERBOSE | re.DOTALL,
    )

    while True:
        new_html_doc = re.sub(SCRIPT_IN_HEAD_REGEX, r"\g<before>\g<after>", html_doc)
        if new_html_doc == html_doc:
            return new_html_doc
        html_doc = new_html_doc


def parse_dt_str(timestr: str) -> str:
    """Parse datestring in ISO format.

    Given a datetime string in any format, attempt to convert it to ISO 8601
    format: https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat
    """
    try:
        dt = dateutil.parser.parse(timestr)
        return dt.isoformat()
    except dateutil.parser.ParserError:
        LOGGER.error(
            "dateutil.parser.ParserError: Date string parsing failed for: {}".format(timestr)
        )
        # TODO: any fallback?
        return None
    except TypeError:  # if tzinfos passed something that is not a timezone
        LOGGER.error("TypeError: Date string parsing failed for: {}".format(timestr))
        # TODO: logging
        return None


def validate_url(url: str) -> bool:
    """Validate the URL and returns True if valid-looking, else False."""
    if url is None:
        return False
    try:
        validate = URLValidator()
        validate(url)
        return True
    except ValidationError:
        return False


def get_xpath_selector_of_soup_tag(
    element: bs4.element.PageElement,
    reduced: bool = False,
) -> str:
    """Generate xpath of soup element.

    Args:
        element: bs4.element.PageElement
            The bs4.element.Tag or bs4.element.NavigableString element.
        reduced: bool (default False)
            Whether to output a reduced version (without numbers).

    Returns:
        xpath: str
            The xpath of that element.
    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        """
        @type parent: bs4.element.Tag
        """
        previous = itertools.islice(parent.children, 0, parent.contents.index(child))
        xpath_tag = child.name
        xpath_index = sum(1 for i in previous if i.name == xpath_tag) + 1
        components.append(
            xpath_tag
            if (xpath_index == 1 or reduced)
            else "{}[{}]".format(xpath_tag, xpath_index)
        )
        child = parent
    components.reverse()
    return "/{}".format("/".join(components))


def get_css_selector_of_soup_tag(
    element: bs4.element.PageElement,
    reduced: bool = False,
) -> str:
    """Generate CSS selector of soup element.

    Args:
        element: bs4.element.PageElement
            The bs4.element.Tag or bs4.element.NavigableString element.
        reduced: bool (default False)
            Whether to output a reduced version (without numbers).

    Returns:
        css_selector: str
            The CSS selector of that element.
    """
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        """
        @type parent: bs4.element.Tag
        """
        previous = itertools.islice(parent.children, 0, parent.contents.index(child))
        css_tag = child.name
        css_index = sum(1 for i in previous if i.name == css_tag) + 1
        components.append(
            css_tag
            if (css_index == 1 or reduced)
            else "{}:nth-child({})".format(css_tag, css_index)
        )
        child = parent
    components.reverse()
    return " > ".join(components)


def get_child_text(tag: bs4.element.Tag) -> str:
    # https://dom.spec.whatwg.org/#concept-child-text-content
    return "".join([x for x in tag.contents if isinstance(tag, bs4.element.NavigableString)])


def extend_config(config, config_items):
    for key, value in config_items.items():
        if hasattr(config, key):
            setattr(config, key, value)
    return config