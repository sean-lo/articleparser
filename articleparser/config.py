"""Defines a configuration object, containing mutable parameters.

Written January 2021.
"""

import logging

from articleparser.settings import (
    DECOMPOSE_TAGS,
    MARKUP_TAGS,
)

LOGGER = logging.getLogger(__name__)


class Config(object):
    def __init__(self):
        # A list of tag names to decompose.
        # This list should not contain "br".
        self.DECOMPOSE_TAGS = DECOMPOSE_TAGS
        # A list of tag names to unwrap.
        # This list should be chosen from tags in `PHRASING_TAGS`. This list should not contain "a".
        self.MARKUP_TAGS = MARKUP_TAGS

        # Whether tags (as defined in `DECOMPOSE_TAGS`) and comments are decomposed (default True)
        self.decompose = True
        # Whether to decompose tags with CSS attributes 'display:none' or 'visibility:hidden' (default True).
        self.cssvis = True
        # Whether to remove "br" tags (default True).
        self.replace_breaks = True
        # Whether to unwrap markup tags (default True).
        self.unwrap_markup = True
        # Whether to calculate link density for nodes (default True).
        self.get_linkdensity = True

        self.LINKDENSITY_UPPERBOUND = 0.75
        self.MAX_LEVELS = 5
        self.MIN_TAGS_TO_CHECK = 1
        self.BASE_TAG_CHARS_RATIO = 0.4
        self.ARTICLE_TEXT_CHARS_RATIO = 0.1
