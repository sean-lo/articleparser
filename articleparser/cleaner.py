"""Cleaning of `bs4.BeautifulSoup` objects as HTML documents.

This module contains the `Cleaner` class that performs customizable 
cleaning of HTML documents, required before content extraction.

Written February 2021.
"""

# Python 3.7 onwards, for annotations with standard collections
from __future__ import annotations

import copy
import logging
import re

import bs4

from articleparser.config import Config
from articleparser.settings import (
    SECTIONING_TAGS,
    IMAGE_AND_MULTIMEDIA_TAGS,
    EMBEDDED_CONTENT_TAGS,
    LEFT_NOSPACE_PUNCTUATION,
    RIGHT_NOSPACE_PUNCTUATION,
)
from articleparser.util import extend_config

LOGGER = logging.getLogger(__name__)


class Cleaner:
    """Perform initial processing on HTML.

    Written February 2021.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        The `bs4.BeautifulSoup` object representing the document.
    uuid : str, optional
        An identifier of the HTML document, for external use.
    config : articleparser.config.Config, optional
        A Config object consisting optional settings.

    Attributes
    ----------
    self.soup : bs4.BeautifulSoup
        The `bs4.BeautifulSoup` object representing the document.

    Methods
    -------
    decompose_tags()
        Decompose tags from given list in `self.soup`.
    decompose_comments()
        Decompose HTML comments in `self.soup`.
    decompose_header_footer()
        Removes the main <header> and <footer> elements of the page.
    clear_invisible()
        Decompose all tags in `self.soup` that are not visible by CSS style.
    remove_whitespace()
        Remove whitespace from the parsed HTML.
    replace_breaks()
        Remove line break tags <br> from HTML.
    unwrap_tags()
        Unwrap tags from `unwrap_tags` in `self.soup`, preserving content.
    get_linkdensity()
        Get link density for all tags in `self.soup`.
    clean()
        Cleans HTML document and returns the `bs4.BeautifulSoup` object.
    """

    def __init__(
        self,
        soup: bs4.BeautifulSoup,
        uuid: str = None,
        config: Config = None,
        **kwargs,
    ):
        self.soup = soup
        self.uuid = uuid
        self.config = config or Config()
        self.config = extend_config(self.config, kwargs)

    def decompose_tags(
        self,
        decompose_tags: list[str],
    ) -> None:
        """Decompose tags from given list in `self.soup`.

        Written December 2020.

        Parameters
        ----------
        decompose_tags : list[str]
            Tag names to decompose.
        Returns
        -------
        None
        """
        for tag in self.soup.find_all(decompose_tags):
            tag.decompose()
        return

    def decompose_comments(self) -> None:
        """Decompose HTML comments in `self.soup`."""
        for tag in self.soup.find_all(text=lambda text: isinstance(text, bs4.Comment)):
            tag.extract()
        return

    def decompose_header_footer(self) -> None:
        """Removes the main <header> and <footer> elements of the page.

        Performs a breadth-first search on page elements, to find the first
        <header> and <footer> tag. If these tags do not have a parent in
        `SECTIONING_TAGS`, decompose them.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        queue = [self.soup]
        header_found = False
        footer_found = False
        while queue and ((not header_found) or (not footer_found)):
            # remove element from front of queue
            element = queue.pop(0)
            if isinstance(element, bs4.element.Tag):
                # finds outermost "header" if not yet found,
                # which does not have a parent in SECTIONING_TAGS
                if not header_found:
                    if element.name == "header":
                        header_found = True
                        parent_set = set(p.name for p in element.parents)
                        if all((x not in parent_set for x in SECTIONING_TAGS)):
                            element.decompose()
                            continue  # skips appending children
                # finds outermost "footer" if not yet found,
                # which does not have a parent in SECTIONING_TAGS
                if not footer_found:
                    if element.name == "footer":
                        footer_found = True
                        parent_set = set(p.name for p in element.parents)
                        if all((x not in parent_set for x in SECTIONING_TAGS)):
                            element.decompose()
                            continue  # skips appending children
            # append child elements if any to back of queue
            if hasattr(element, "children"):
                for child in element.children:
                    queue.append(child)

        return

    @staticmethod
    def _parse_style_string(style_string: str) -> dict[str, str]:
        # Convert string representing CSS style into a dict with key-value pairs
        # separated by `;`, and keys separated from values by `:`.
        # Return the style dictionary.
        style_dict = {}
        # print(style_string)
        for kv in style_string.split(";"):
            kv = kv.strip()
            if kv == "":
                break
            for c in ["{", "}", ";"]:
                assert c not in kv  # TODO: exposed assert
            try:
                k, v = kv.split(":", maxsplit=1)
                style_dict[k.strip()] = v.strip()
            except:
                pass
        return style_dict

    @staticmethod
    def _is_cssvis_invisible(tag: bs4.element.Tag) -> bool:
        # Return True if the tag has style attribute `display:none` or
        # `visibility:hidden`, False otherwise
        HTML_SMALL_LENGTHS = r"(0|1)(px)?(\s!important)?"

        if "hidden" in tag.attrs:
            return True
        elif "style" in tag.attrs:
            style_string = tag.attrs["style"]
            style_dict = Cleaner._parse_style_string(style_string)
            if (sd_display := style_dict.get("display")) :
                if re.fullmatch(r"none(\s!important)?", sd_display):
                    return True
            elif (sd_visibility := style_dict.get("visibility")) :
                if re.fullmatch(r"hidden(\s!important)?", sd_visibility):
                    return True
            elif (sd_width := style_dict.get("width")) :
                if re.fullmatch(HTML_SMALL_LENGTHS, sd_width):
                    return True
            elif (sd_height := style_dict.get("height")) :
                if re.fullmatch(HTML_SMALL_LENGTHS, sd_height):
                    return True
            elif style_dict.get("opacity") in ["0", "0 !important"]:
                return True

        if (width := tag.get("width")) :
            if re.fullmatch(HTML_SMALL_LENGTHS, width):
                return True
        elif (height := tag.get("height")) :
            if re.fullmatch(HTML_SMALL_LENGTHS, height):
                return True
        elif tag.get("role") in ["presentation", "none"]:
            return True
        return False

    def clear_invisible(
        self,
        tag: bs4.element.Tag,
    ) -> None:
        """Decompose all tags in `self.soup` that are not visible by CSS style.

        All tags with the CSS style attribute `display:none` or
        `visibility:hidden` are detected via _is_cssvis_invisible()
        and decomposed.

        A recursive implementation is used.

        Written December 2020.

        Parameters
        ----------
        tag : bs4.element.Tag
            The current tag to consider.

        Returns
        -------
        None
        """
        for child_node in tag.contents:
            if isinstance(child_node, bs4.element.Tag):
                if Cleaner._is_cssvis_invisible(child_node):
                    child_node.decompose()
                else:
                    self.clear_invisible(child_node)
        return

    @staticmethod
    def _is_whitespace_nstring(node: bs4.element.PageElement) -> bool:
        """Checks if node is a `bs4.element.NavigableString` instance that is
        empty or fully whitespace."""
        return (
            isinstance(node, bs4.element.NavigableString)
            and re.fullmatch(r"\s*", node) is not None
        )

    @staticmethod
    def _is_nonwhitespace_nstring(node: bs4.element.PageElement) -> bool:
        """Checks if node is a `bs4.element.NavigableString` instance that is
        nonempty and not fully whitespace."""
        return (
            # if node is None, this returns False
            isinstance(node, bs4.element.NavigableString)
            and (re.fullmatch(r"\s*", node) is None)
        )

    def remove_whitespace(self) -> None:
        """Remove whitespace from the parsed HTML.

        1) Extracts (deletes) all `bs4.element.NavigableString` instances that
           are fully whitespace (for example, "\n").
        2) Strips all other `bs4.element.NavigableString` instances of leading
           and trailing whitespace.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        for tag in self.soup.find_all(True):
            for node in tag.contents:
                if self._is_whitespace_nstring(node):
                    # node is fully whitespace NavigableString
                    node.extract()
                elif isinstance(node, bs4.element.NavigableString):
                    stripped_string = node.strip()
                    node.replace_with(stripped_string)
        return

    def replace_breaks(self) -> None:
        """Remove line break tags <br> from HTML.

        If <br/> happens within a parent tag, and both its siblings are
        non-whitespace text, "close and reopen" the parent tag in its place.
        Otherwise just delete it.

        Should be performed after `remove_whitespace()` in order for the
        neighbour check to work as intended.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        while True:
            br = self.soup.find("br")
            if br is None:
                break
            
            # condition for splitting the parent tag
            # fmt: off
            if (
                self._is_nonwhitespace_nstring(br.previous_sibling)
                and self._is_nonwhitespace_nstring(br.next_sibling)
            ):
            # fmt: on
                # obtain the contents list and split in two,
                # excluding the <br/> element
                contents_list = br.parent.contents
                br_index = contents_list.index(br)

                left_contents_list = contents_list[:br_index]
                right_contents_list = contents_list[br_index + 1 :]

                # make two copies of the parent tag and attributes
                # remove `id` attribute from right tag if exists
                left_tag = copy.copy(br.parent)
                right_tag = copy.copy(br.parent)
                if right_tag.get("id"):
                    del right_tag["id"]

                # set contents of left_tag and right_tag to
                # their halves of contents_list respectively
                left_tag.clear()
                right_tag.clear()
                left_tag.extend(left_contents_list)
                right_tag.extend(right_contents_list)

                # insert left_tag and right_tag to their positions in the tree,
                # then remove the parent tag
                br.parent.insert_before(left_tag)
                br.parent.insert_after(right_tag)

                br.parent.decompose()
                continue
            else:  # condition for just removing
                br.decompose()
                continue
        return

    def unwrap_tags(
        self,
        unwrap_tags: list[str],
        adjust_spacing: bool = False,
    ) -> None:  # default behaviour is: this is not removed
        """Unwrap tags from `unwrap_tags` in `self.soup`, preserving content.

        For each tag, the left and right siblings are modified to ensure the
        correct amount of whitespace.

        Written December 2020.

        Parameters
        ----------
        unwrap_tags: list[str]
            A list of tags to unwrap.
        adjust_spacing: bool, default False
            Whether to adjust spacing beside unwrapped tag.

        Returns
        -------
        None
        """
        for tag in self.soup.find_all(unwrap_tags):
            if adjust_spacing:
                # modify those adjacent siblings if NavigableString
                current = tag
                while True:
                    left = current.previous_sibling
                    if left:
                        break
                    else:
                        current = current.parent
                if left:
                    while isinstance(left, bs4.element.Tag):
                        if len(left.contents) > 0:
                            left = left.contents[-1]
                        else:
                            break
                    if isinstance(left, bs4.element.NavigableString):
                        newleft = left.rstrip()
                        if len(newleft) > 0:
                            if newleft[-1] not in LEFT_NOSPACE_PUNCTUATION:
                                newleft = newleft + " "
                        left.replace_with(newleft)
                current = tag
                while True:
                    right = current.next_sibling
                    if right:
                        break
                    else:
                        current = current.parent
                if right:
                    while isinstance(right, bs4.element.Tag):
                        if len(right.contents) > 0:
                            right = right.contents[0]
                        else:
                            break
                    if isinstance(right, bs4.element.NavigableString):
                        newright = right.lstrip()
                        if len(newright) > 0:
                            if newright[0] not in RIGHT_NOSPACE_PUNCTUATION:
                                newright = " " + newright
                        right.replace_with(newright)
            tag.unwrap()
        return

    @staticmethod
    def _text_from_subtree(tag: bs4.element.Tag) -> str:
        # Given a bs4.element.Tag, return all stripped strings joined by `\n`.
        return "\n".join(tag.stripped_strings)

    def _decompose_empty(self) -> None:
        # Decompose empty tags (with no text content) in self.soup
        # This method should only be called when _get_linkdensity() has been
        # called on self.soup.
        def is_empty(tag):
            if tag["_ld_tc"] == 0:
                if len(list(tag.find_all(
                    IMAGE_AND_MULTIMEDIA_TAGS + EMBEDDED_CONTENT_TAGS
                ))) == 0:
                    if (
                        tag.name
                        not in IMAGE_AND_MULTIMEDIA_TAGS + EMBEDDED_CONTENT_TAGS
                    ):
                        return True
            return False

        for tag in self.soup.find_all(is_empty):
            tag.decompose()
        return

    @staticmethod
    def _get_link_chars(tag: bs4.element.Tag) -> int:
        # Recursively get number of `link_chars` (characters in anchor tags).
        if "_ld_lc" in tag.attrs:  # if _ld_lc computed already, retrieve
            return int(tag["_ld_lc"])
        else:  # _ld_lc not yet computed, compute and store in _ld_lc
            # if node itself is an anchor tag, its `link_chars` is its
            # `total_chars`
            if tag.name == "a":
                # set its own link characters
                lc = Cleaner._get_total_chars(tag)
                tag["_ld_lc"] = lc
                for child_tag in tag.find_all(True):
                    # calculate / set total characters for child tag(s)
                    tc = Cleaner._get_total_chars(child_tag)
                    # set link characters for child tag(s)
                    child_tag["_ld_lc"] = tc
                return lc
            else:
                lc = 0
                # Sum over `link_chars` of direct children tags only
                for child_tag in tag.find_all(recursive=False):
                    lc += Cleaner._get_link_chars(child_tag)
                tag["_ld_lc"] = lc
                return lc

    @staticmethod
    def _get_total_chars(tag: bs4.element.Tag) -> int:
        # Recursively get number of `total_chars` (characters in all tags).
        if "_ld_tc" in tag.attrs:  # if _ld_tc computed already, retrieve
            return int(tag["_ld_tc"])
        else:  # _ld_tc not yet computed, compute and store in _ld_tc
            tc = 0
            # Sum over `total_chars` of direct children nodes only
            for child in tag.contents:
                if isinstance(child, bs4.element.Tag):
                    tc += Cleaner._get_total_chars(child)
                elif isinstance(child, bs4.element.NavigableString):
                    tc += len(child.strip())
            tag["_ld_tc"] = tc
            return tc

    @staticmethod
    def _get_linkdensity(tag: bs4.element.Tag) -> float:
        # Recursively calculate `link_density`, returns float
        # `link_density` is ratio of `link_chars` to `total_chars` of tag
        if "_linkdensity" in tag.attrs:
            return float(tag["_linkdensity"])
        else:
            # attempts to get link_chars and total_chars; this will trigger
            # the start of calculations for all tags in tag
            lc = Cleaner._get_link_chars(tag)
            tc = Cleaner._get_total_chars(tag)
            if tc > 0:
                d = float(lc / tc)
            else:
                # tc can be 0 if tags that are empty are encountered
                d = 0.0
            tag["_linkdensity"] = d
            return d

    def get_linkdensity(self) -> None:
        """Get link density for all tags in `self.soup`.

        The link_density for the whole self.soup is first computed.
        Thereafter, empty tags (with zero total characters) are decomposed;
        and link_density for each tag in the soup is then computed.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # computes `_ld_lc` and `_ld_tc` for each tag
        self._get_linkdensity(self.soup)

        # can only be done after _get_linkdensity(self.soup)
        # (since it requires `_ld_tc` to be computed)
        # but must be before _get_linkdensity(tag) (to avoid ZeroDivisionError)
        self._decompose_empty()

        for tag in self.soup.find_all(True):
            self._get_linkdensity(tag)
        return

    def clean(self) -> None:
        """Cleans HTML document and returns the `bs4.BeautifulSoup` object.

        Written February 2021.

        Returns
        -------
        None
        """
        if self.soup is None:
            LOGGER.error("No soup supplied for: {}!".format(self.uuid))
            return
        if self.config.decompose:
            self.decompose_tags(self.config.DECOMPOSE_TAGS)
            self.decompose_comments()
            self.decompose_header_footer()
            LOGGER.debug("Decomposed tags, and removed HTML comments!")
        if self.config.cssvis:
            self.clear_invisible(self.soup.body)
            LOGGER.debug(
                "Cleared tags with CSS attributes 'display: none' or 'visibility: hidden'!"
            )
        self.soup.smooth()
        # remove whitespace before removing breaks, because of the
        # neighbour check in remove_breaks
        self.remove_whitespace()
        if self.config.replace_breaks:
            self.replace_breaks()
            LOGGER.debug("Removed <br> tags!")

        if self.config.unwrap_markup:
            self.unwrap_tags(self.config.MARKUP_TAGS)
            LOGGER.debug("Stripped HTML markup from file!")
        self.soup.smooth()
        if self.config.get_linkdensity:
            self.get_linkdensity()
            self.soup.smooth()
            LOGGER.debug("Calculated link density for all nodes!")
        return
