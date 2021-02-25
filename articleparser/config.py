"""Defines a configuration object, containing mutable parameters.

Written February 2021.
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
        # This list should be chosen from tags in `PHRASING_TAGS`.
        # This list should not contain "a".
        self.MARKUP_TAGS = MARKUP_TAGS

        # Whether tags (as defined in `DECOMPOSE_TAGS`) and comments are
        # decomposed (default True)
        self.decompose = True
        # Whether to decompose tags with CSS attributes 'display:none' or
        # 'visibility:hidden' (default True).
        self.cssvis = True
        # Whether to remove "br" tags (default True).
        self.replace_breaks = True
        # Whether to unwrap markup tags (default True).
        self.unwrap_markup = True
        # Whether to calculate link density for nodes (default True).
        self.get_linkdensity = True

        # Controls the ratio at which a tag is considered "hyperlink-heavy",
        # both in the detection of `top_tag` in `set_top_tag()`
        # and in the subsequent removal of hyperlink-heavy sections.
        self.LINKDENSITY_UPPERBOUND = 0.75

        # In the detection of `top_tag`, in `_get_best_common_ancestor()`:
        # Controls the levels of nesting that is "acceptable", such that
        # `top_tag` is at most `MAX_LEVELS` levels away from paragraph tags.
        # A larger number (e.g. 8) would be useful for certain HTML structures
        # with clusters of paragraphs grouped together, to find all paragraphs.
        self.MAX_LEVELS = 5

        # In the detection of `top_tag`, in `set_top_tag()`:
        # Determines the number of tags in `tags_to_check` required
        # for the check to proceed;
        # Setting this to a higher number will reduce the likelihood of
        # detecting single-tag articles, but one may miss out on short articles.
        self.MIN_TAGS_TO_CHECK = 1

        # In the determination of `base_tag`:
        # Determines the minimum proportion of characters to the HTML body that
        # the `base_tag` contains.
        # For each choice found from `BASE_TAG_SELECTORS`, if the proportion of
        # characters is less than this ratio, the next choice is considered.
        # Setting this to be smaller runs the risk of including non-"base_tag"s
        # such as those for related articles;
        # Setting this to be higher runs the risk of missing out on legitimate
        # "base_tag"s surrounded by a lot of other content.
        self.BASE_TAG_CHARS_RATIO = 0.4

        # In `get_article_text()`:
        # Determines the minimum proportion of characters to the HTML body that
        # the paragraphs in `top_tag` contain.
        # For each choice for the paragraphs in `TEXT_TO_COLLECT_LISTS`,
        # if the proportion of characters is less than this ratio,
        # the next choice is considered.
        # Setting this to be higher runs the risk of the check failing and
        # including junk from less relevant tags from `TEXT_TO_COLLECT_LISTS`;
        # Setting this to be lower runs the risk of including "single-word"
        # paragraphs from other places instead of the main article content.
        self.ARTICLE_TEXT_CHARS_RATIO = 0.1
