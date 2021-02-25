"""Implements the `Article` class, representing a news article.

The `Article` class has a `parse()` method which extracts structured data
from a HTML document, provided in the form of a `bs4.BeautifulSoup` object.

Written February 2021.
"""

# Python 3.7 onwards, for annotations with standard collections
from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any, Union

import bs4

from articleparser.cleaner import Cleaner
from articleparser.config import Config
from articleparser.extractor import ArticleExtractor
from articleparser.metadata import extract_metadata
from articleparser.util import (
    make_soup,
    extend_config,
)

LOGGER = logging.getLogger(__name__)


class Article(object):
    """Represents a web article.

    Contains the `parse()` method, which parses a web article represented as
    a `bs4.BeautifulSoup` object, and obtains structured data from it.

    Written February 2021.

    Parameters
    ----------
    filepath : str
        The filepath containing the HTML document.
    soup : bs4.BeautifulSoup, optional
        The `bs4.BeautifulSoup` object representing the document.
        If None, will be loaded from `filepath` with `make_soup()`.
    uuid : str, optional
        An identifier of the HTML document, for external use.
    config : articleparser.config.Config, optional
        A Config object consisting optional settings.
    **kwargs : optional
        Extra optional arguments to extend `config`.

    Attributes
    ----------
    filepath
    uuid
    config
    soup : bs4.BeautifulSoup
        The `bs4.BeautifulSoup` object stored at `filepath`, as loaded by
        `make_soup()`.
    backup_soup : bs4.BeautifulSoup
        The `bs4.BeautifulSoup` object stored at `filepath`, as loaded by
        `make_soup()`.
    article_url : str
        The article URL obtained from extraction.
    cleaner : articleparser.cleaner.Cleaner
        The `Cleaner` object for this document.
    extractor : articleparser.extractor.ArticleExtractor
        The `ArticleExtractor` object for this document.
    content : dict[str, Any]
        The extracted content of this article.
        Contains the following keys from `CONTENT_FIELDS`:
        "record_categories_list": list[str], each non-empty
        "author_list" : list[dict], possibly empty,
                        each with the following keys:
            "name" : str, non-empty
            "url" : str (validated by validate_url()) or None
            "image_url" : str (validated by validate_url()) or None
        "record_title" : str, non-empty or None
        "record_url" : str (validated by validate_url())
        "record_published_isotimestamp" : str in ISO 8601 format or None
        "record_modified_isotimestamp" : str in ISO 8601 format or None
        "site": dict(str) with the following keys:
            "name": str, non-empty or None
            "url": str (validated by validate_url()) or None
        "record_language": str, non-empty or None
        "record_content": str, non-empty or None
        "record_description": str, non-empty or None
        "record_images_list": list[dict], possibly empty,
                             each with the following keys:
            "url": str (validated by validate_url())
            "alt_text": str, non-empty or None
        "record_links_list": list[dict], possibly empty,
                             each with the following keys:
            "url": str (validated by validate_url())
            "text": str, non-empty
        "record_videos_list": list[dict], possibly empty,
                              each with the following keys:
            "url": str (validated by validate_url())
            "alt_text": str, non-empty or None
        "record_documents_list": list[dict], possibly empty,
                              each with the following keys:
            "url": str (validated by validate_url())
            "alt_text": str, non-empty or None
        "record_keywords_list": list[str], each non-empty
        "record_comment_areas_list": list[dict], possibly empty,
                              each with the following keys:
            "url": str (validated by validate_url())
            "alt_text": str, non-empty or None
    methods : dict[str, Any]
        The method of extraction for fields in `content`.

    Methods
    -------
    parse()
        Parses article into content fields.

    See Also
    --------
    articleparser.util.make_soup :
        Custom function parsing a HTML document.
    articleparser.metadata.extract_metadata :
        function extracting metadata from HTML.
    articleparser.extractor.ArticleExtractor :
        Extraction routines from `self.soup` and `metadata`.
    articleparser.cleaner.Cleaner
        Cleans HTML.
    """

    CONTENT_FIELDS = [
        "record_categories_list",
        "author_list",
        "record_title",
        "record_url",
        "record_published_isotimestamp",
        "record_modified_isotimestamp",
        "site",
        "record_language",
        "record_content",
        "record_description",
        "record_images_list",
        "record_links_list",
        "record_videos_list",
        "record_documents_list",
        "record_keywords_list",
        "record_comment_areas_list",
    ]

    def __init__(
        self,
        *,  # all arguments are keyword-only
        filepath: Union[str, Path] = None,
        soup: bs4.BeautifulSoup = None,
        uuid: str = None,
        config: Config = None,
        **kwargs,
    ):
        if isinstance(filepath, str):
            filepath = Path(filepath)
        self.filepath = filepath

        if soup:
            self.soup = soup
            self.backup_soup = copy.copy(soup)
        elif filepath:
            self.soup = make_soup(self.filepath)
            self.backup_soup = make_soup(self.filepath)
        else:
            raise ValueError("Must provide at least one of filepath and soup!")

        if uuid:
            self.uuid = uuid
        else:
            self.uuid = str(filepath)

        self.config = config or Config()
        self.config = extend_config(self.config, kwargs)

        self.article_url = None

        self.cleaner = None
        self.extractor = None

        self.content = dict.fromkeys(self.CONTENT_FIELDS)
        self.methods = {}

    def parse(self) -> None:
        """Parses article into content fields.

        First, collects HTML metadata from `self.soup` via `extract_metadata()`.
        Next, initializes an `ArticleExtractor` object and uses it to extract
        short fields from `self.soup` and `metadata`.
        Then, initializes a `Cleaner` object to clean the HTML document,
        before performing asset extraction and content extraction with
        `ArticleExtractor`. Collected data is stored in `self.content`.

        Written February 2021.

        Parameters
        ----------
        None

        Returns
        -------
        None

        See Also
        --------
        articleparser.metadata.extract_metadata :
            function extracting metadata from HTML.
        articleparser.extractor.ArticleExtractor :
            Extraction routines from `self.soup` and `metadata`.
        articleparser.cleaner.Cleaner
            Cleans HTML.
        """
        LOGGER.info("Parsing article from: {}".format(self.uuid))

        if self.soup is None:
            LOGGER.error("Soup parsing failed for: {}".format(self.uuid))
            return

        # code for content extraction from soup.head
        metadata = extract_metadata(self.soup, self.uuid)
        LOGGER.debug("Collected article metadata.")

        self.extractor = ArticleExtractor(
            soup=self.soup,
            metadata=metadata,
            config=self.config,
        )

        # record_url
        (
            self.content["record_url"],
            self.methods["record_url"],
        ) = self.extractor.extract_page_url()
        self.article_url = self.content["record_url"]

        ### cleaning HTML ###
        self.cleaner = Cleaner(
            soup=self.soup,
            config=self.config,
            unwrap_markup=False,
        )
        self.cleaner.clean()
        self.soup = self.cleaner.soup
        ###

        # record_title
        (
            self.content["record_title"],
            self.methods["record_title"],
        ) = self.extractor.extract_title(clean=True)

        # record_published_isotimestamp and record_modified_isotimestamp
        timestamps, timestamps_methods = self.extractor.extract_timestamps()
        self.content.update(timestamps)
        self.methods.update(timestamps_methods)
        # site_name
        # fmt: off
        self.content["site"] = (
            metadata["json_ld"]["publisher"]
            or [{
                "name": metadata["opengraph"].get("og:site_name"),
                "url": None,
            }]
        )
        # fmt: on

        # record_language
        (
            self.content["record_language"],
            self.methods["record_language"],
        ) = self.extractor.extract_language()

        # record_description
        (
            self.content["record_description"],
            self.methods["record_description"],
        ) = self.extractor.extract_description()
        # record_keywords_list
        (
            self.content["record_keywords_list"],
            self.methods["record_keywords_list"],
        ) = self.extractor.extract_keywords()
        # record_categories_list
        # fmt: off
        self.content["record_categories_list"] = (
            metadata["json_ld"].get("articleSection")
            or [metadata["opengraph"].get("article:section")]
        )
        # fmt: on

        ### section on retrieving top node ###
        self.extractor.soup = self.soup

        self.extractor.set_base_tag()
        base_tag = self.extractor.base_tag
        self.extractor.set_top_tag()
        top_tag = self.extractor.top_tag
        ###

        # record_images_list
        self.extractor.get_pictures()
        self.content["record_images_list"] = [
            {
                "url": image_item.get("src"),
                "alt_text": image_item.get("alt"),
            }
            for image_item in self.extractor.image_list
        ]
        self.extractor.get_assets()
        # record_links_list
        self.content["record_links_list"] = self.extractor.links_list
        # record_videos_list
        self.content["record_videos_list"] = [
            {
                "url": video_item.get("video_url"),
                "alt_text": None,
            }
            for video_item in self.extractor.video_list
        ]
        self.content["record_comment_areas_list"] = self.extractor.comment_area_list
        self.extractor.get_documents()
        self.content["record_documents_list"] = [
            {
                "url": document_item.get("url"),
                "alt_text": document_item.get("text"),
            }
            for document_item in self.extractor.document_list
        ]

        ###
        # getting article text and inline links
        article_text = self.extractor.get_article_text()
        ###

        # record_content
        self.content["record_content"] = article_text
        self.content["record_links_list"].extend(self.extractor.inline_links_list)

        # author_list
        (
            self.content["author_list"],
            self.methods["author_list"],
        ) = self.extractor.extract_authors()

        LOGGER.debug("Extraction complete.")
        return None