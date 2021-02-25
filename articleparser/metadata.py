"""Extraction of content from HTML metadata.

This module contains all functions extracting document metadata from a
HTML document; fitting data into schema are outside the scope of this module
and belongs in extractor.py instead.

Written February 2021.

Routine Listings
----------------
extract_opengraph(soup, uuid)
    Extract metadata from OpenGraph Protocol tags (https://ogp.me/).
extract_json_ld_dictlist(soup, uuid)
    Extract nodes from JSON-LD named graphs.
extract_json_ld(soup, uuid)
    Extract metadata from JSON-LD data format (https://json-ld.org/).
extract_metadata(soup, uuid)
    Wrapper function around all metadata extraction functions.
"""

# Python 3.7 onwards, for annotations with standard collections
from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from typing import Any, Union, Optional
from urllib.parse import urljoin

import bs4

from articleparser.util import (
    parse_dt_str,
    validate_url,
)

LOGGER = logging.getLogger(__name__)


def extract_opengraph(
    soup: bs4.BeautifulSoup,
    uuid: str = None,
) -> dict[str, Union[str, list[str], None]]:
    """Extract metadata from OpenGraph Protocol tags (https://ogp.me/).

    <meta> tags following this protocol have HTML attribute `property`
    beginning with "og:" (or some other prefix, but this is the most common),
    and HTML attribute `content` with the value of this OGP property.
    Alternatively, `property` can have a "article:" prefix but it must then
    have an "og:type" value of "article".
    Other namespaces exist.

    Written February 2021.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        The `bs4.BeautifulSoup` object representing the HTML document.
    uuid : str, optional
        An identifier of the HTML document, for external use.

    Returns
    -------
    metadata_ogp : dict
        A dict with the following keys and non-empty values, if present;
        else None:
        "og:title" : str, non-empty or None
        "og:type" : str, non-empty or None
        "og:description" : str, non-empty or None
        "og:locale" : str, non-empty or None
        "og:site_name" : str, non-empty or None
        "og:images" : list[dict[str, str]], possibly empty:
                      each item is a dict with some of the following
                      key-value pairs:
            "og:image" : str
            "og:image:url" : str or None
            "og:image:secure_url" : str or None
            "og:image:type" : str or None
            "og:image:width" : str or None
            "og:image:height" : str or None
            "og:image:alt" : str or None
        "og:videos" : list[dict[str, str]], possibly empty:
                      each item is a dict with some of the following
                      key-value pairs:
            "og:video" : str
            "og:video:url" : str or None
            "og:video:secure_url" : str or None
            "og:video:type" : str or None
            "og:video:width" : str or None
            "og:video:height" : str or None
            "og:video:alt" : str or None
        "og:url" : str (validated by validate_url())
        "og:locale:alternate" : list[str]
        (and if "og:type" is "article", additionally the following:)
        "article:published_time" : str
        "article:modified_time" : str
        "article:expiration_time" : str
        "article:section" : str
        "article:tag" : list[str] (possibly empty)
        "article:author" : list[str] (possibly empty)
    """
    metadata_ogp = {}
    metadata_ogp["og:images"] = []
    metadata_ogp["og:videos"] = []
    metadata_ogp["og:locale:alternate"] = []
    metadata_ogp["article:tag"] = []
    metadata_ogp["article:author"] = []

    image_item = {}
    # all <meta> tags in <head> with property value beginning with 'og:image'
    for tag in soup.select("head meta[property^='og:image']"):
        content = tag.get("content")
        if content is None:
            continue
        prop = tag.get("property")
        if prop == "og:image":
            # append previous image item to the list, if any
            if image_item.get("og:image"):
                metadata_ogp["og:images"].append(image_item)
                # re-initialize image_item
                # https://ogp.me/#array
                image_item = {"og:image": content}
            else:
                image_item["og:image"] = content
        else:
            if prop in [
                "og:image:url",
                "og:image:secure_url",
                "og:image:type",
                "og:image:width",
                "og:image:height",
                "og:image:alt",
            ]:
                image_item[prop] = content
    # append last found image item, if it exists
    if image_item.get("og:image"):
        metadata_ogp["og:images"].append(image_item)

    video_item = {}
    for tag in soup.select("head meta[property^='og:video']"):
        content = tag.get("content")
        if content is None:
            continue
        prop = tag.get("property")
        if prop == "og:video":
            # append previous video item to the list, if any
            if video_item.get("og:video"):
                metadata_ogp["og:videos"].append(video_item)
                # re-initialize video_item
                # https://ogp.me/#array
                video_item = {"og:video": content}
            else:
                video_item["og:video"] = content
        else:
            if prop in [
                "og:video:url",
                "og:video:secure_url",
                "og:video:type",
                "og:video:width",
                "og:video:height",
                "og:video:alt",
            ]:
                video_item[prop] = content

    # detect OpenGraph schema
    for tag in soup.select("head meta[property^='og:']"):
        content = tag.get("content")
        if content is None:
            continue
        prop = tag.get("property")
        if isinstance(content, str):
            content = content.strip()
            if len(content) > 0:
                if prop in [
                    "og:title",
                    "og:type",
                    "og:description",
                    "og:site_name",
                ]:
                    metadata_ogp[prop] = content
                # locales: reformat according to https://tools.ietf.org/html/rfc5646
                elif prop in ["og:locale"]:
                    content = "-".join(content.split("_"))
                    metadata_ogp[prop] = content
                # checks if URL is valid
                elif prop in ["og:url"]:
                    if validate_url(content):
                        metadata_ogp[prop] = content
                # locale_alternate - multiple tags
                elif prop in ["og:locale:alternate"]:
                    content = "-".join(content.split("_"))
                    metadata_ogp[prop].append(content)

    if metadata_ogp.get("og:type") == "article":
        for tag in soup.select("head meta[property^='article:']"):
            content = tag.get("content")
            if content is None:
                continue
            prop = tag.get("property")
            if isinstance(content, str):
                content = content.strip()
                if len(content) > 0:
                    if prop in [
                        "article:published_time",
                        "article:modified_time",
                        "article:expiration_time",
                    ]:
                        metadata_ogp[prop] = parse_dt_str(content)
                    elif prop in ["article:section"]:
                        metadata_ogp[prop] = content
                    elif prop in ["article:tag"]:
                        taglist = [x.strip() for x in content.split(",") if len(x.strip()) > 0]
                        metadata_ogp[prop].extend(taglist)
                    elif prop in ["article:author"]:
                        metadata_ogp[prop].append(content)

    return metadata_ogp


def extract_json_ld_dictlist(
    soup: bs4.BeautifulSoup,
    uuid: str = None,
) -> list[dict[Any]]:
    """Extract nodes from JSON-LD named graphs.

    <script> tags containing this data have HTML attribute `type` and HTML
    attribute value "application/ld+json".

    Nodes group together in named graphs in JSON-LD are first extracted; see
    https://json-ld.org/spec/latest/json-ld/#named-graphs.

    Written February 2021.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        The `bs4.BeautifulSoup` object representing the HTML document.
    uuid : str, optional
        An identifier of the HTML document, for external use.

    Returns
    -------
    json_ld_dictlist : list[dict[Any]]
        A list of dicts, each representing a node in JSON-LD.
    """
    json_ld_dictlist_graph = []
    # recording all items that can be dicts or list of dicts

    for tag in soup.select("script[type='application/ld+json']"):
        try:
            item = json.loads(tag.string, strict=False)
        except json.JSONDecodeError:
            # TODO known issue; need to evaluate "+" as string concatenation
            LOGGER.debug("Could not decode JSON-LD in: {}".format(uuid))
            LOGGER.debug("Tag string: {}".format(tag.string))
            continue
        if isinstance(item, list):
            json_ld_dictlist_graph.extend(item)
        elif isinstance(item, dict):
            json_ld_dictlist_graph.append(item)
        else:
            LOGGER.debug("JSON_LD entry was not of type list or dict, in: {}".format(uuid))
            pass

    json_ld_dictlist = []
    # for all named graphs https://json-ld.org/spec/latest/json-ld/#named-graphs
    for dictitem in json_ld_dictlist_graph:
        if "@graph" in dictitem:
            itemlist = dictitem["@graph"]
            context = dictitem["@context"]
            if isinstance(itemlist, list):
                # https://json-ld.org/spec/latest/json-ld/#example-61-context-needs-to-be-duplicated-if-graph-is-not-used
                for item in itemlist:
                    if "@context" not in item:
                        item["@context"] = context
                    # else:
                    #     print("There was already a context: {}".format(
                    #         item["@context"]))
                    json_ld_dictlist.append(item)
            else:
                LOGGER.debug(
                    "JSON_LD dict contained '@graph' but item was not of type list, in: {}".format(
                        uuid
                    )
                )
        else:
            json_ld_dictlist.append(dictitem)

    return json_ld_dictlist


def extract_json_ld(
    soup: bs4.BeautifulSoup,
    uuid: str = None,
) -> dict[str, Union[str, list[str], list[dict[str, Optional[str]]]]]:
    """Extract metadata from JSON-LD data format (https://json-ld.org/).

    <script> tags containing this data have HTML attribute `type` and HTML
    attribute value "application/ld+json".

    Nodes group together in named graphs in JSON-LD are first extracted
    using `extract_json_ld_dictlist()`; see
    https://json-ld.org/spec/latest/json-ld/#named-graphs.

    Thereafter nodes with "@type" "NewsArticle", "Article" or "WebPage" are
    considered and their attributes unpacked.

    Written February 2021.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        The `bs4.BeautifulSoup` object representing the HTML document.
    uuid : str, optional
        An identifier of the HTML document, for external use.

    Returns
    -------
    metadata_json_ld : \
        dict[str, Union[str, list[str], list[dict[str, Optional[str]]]]]
        A dict with the following keys and non-empty values, if present;
        else None:
        "headline" : str, non-empty or None
        "name" : str, non-empty or None
        "articleBody" : str, non-empty or None
        "articleSection" : list[str], each non-empty
        "description" : str, non-empty or None
        "inLanguage" : str, non-empty or None
        "datePublished" : str, non-empty or None
        "dateModified" : str, non-empty or None
        "dateCreated" : str, non-empty or None
        "url" : str (validated by validate_url())
        "author" : list[dict] (possibly empty) each with the following keys:
            "name" : str, non-empty
            "url" : str (validated by validate_url()) or None
        "publisher" : list[dict] with length <= 1, each with the following keys:
            "name" : str, non-empty
            "url" : str (validated by validate_url()) or None
        "image" : list[str] (each validated by validate_url())
        "keywords" : list[str], each non-empty
    """
    json_ld_dictlist = extract_json_ld_dictlist(soup, uuid)

    # https://schema.org/NewsArticle
    # [NewsArticle, [AnalysisNewsArticle, AskPublicNewsArticle,
    # BackgroundNewsArticle, OpinionNewsArticle,
    # ReportageNewsArticle, ReviewNewsArticle]]
    NEWSARTICLE_SCHEMA = [
        "AnalysisNewsArticle",
        "AskPublicNewsArticle",
        "BackgroundNewsArticle",
        "NewsArticle",
        "OpinionNewsArticle",
        "ReportageNewsArticle",
        "ReviewNewsArticle",
    ]
    # https://schema.org/Article
    # exclude NewsArticle (included above), TechArticle,
    # SocialMediaPosting (below)
    # [Article, [AdvertiserContentArticle, Report, SatiricalArticle,
    # ScholarlyArticle]]
    ARTICLE_SCHEMA = [
        "Article",
        "AdvertiserContentArticle",
        "Report",
        "SatiricalArticle",
        "ScholarlyArticle",
    ]
    # https://schema.org/SocialMediaPosting
    # [SocialMediaPosting, [BlogPosting, [LiveBlogPosting],
    # DiscussionForumPosting]]
    BLOGPOST_SCHEMA = [
        "SocialMediaPosting",
        "BlogPosting",
        "LiveBlogPosting",
        "DiscussionForumPosting",
    ]
    # https://schema.org/WebPage
    WEBPAGE_SCHEMA = [
        "WebPage",
    ]

    sorted_article_dictlist = []

    newsarticlelist = [
        x
        for x in json_ld_dictlist
        if "@type" in x
        and (
            (isinstance(x["@type"], str) and x["@type"] in NEWSARTICLE_SCHEMA)
            or (isinstance(x["@type"], list) and x["@type"][0] in NEWSARTICLE_SCHEMA)
        )
    ]
    if len(newsarticlelist) == 1:
        sorted_article_dictlist.append(newsarticlelist[0])
    elif len(newsarticlelist) == 0:
        LOGGER.debug("No JSON-LD NewsArticle items found!")
    else:
        LOGGER.debug("More than one JSON-LD NewsArticle item found!")

    articlelist = [
        x
        for x in json_ld_dictlist
        if "@type" in x
        and (
            (isinstance(x["@type"], str) and x["@type"] in ARTICLE_SCHEMA)
            or (isinstance(x["@type"], list) and x["@type"][0] in ARTICLE_SCHEMA)
        )
    ]
    if len(articlelist) == 1:
        sorted_article_dictlist.append(articlelist[0])
    elif len(articlelist) == 0:
        LOGGER.debug("No JSON-LD Article items found!")
    else:
        LOGGER.debug("More than one JSON-LD Article item found!")

    blogpostlist = [
        x
        for x in json_ld_dictlist
        if "@type" in x
        and (
            (isinstance(x["@type"], str) and x["@type"] in BLOGPOST_SCHEMA)
            or (isinstance(x["@type"], list) and x["@type"][0] in BLOGPOST_SCHEMA)
        )
    ]
    if len(blogpostlist) == 1:
        sorted_article_dictlist.append(blogpostlist[0])
    elif len(blogpostlist) == 0:
        LOGGER.debug("No JSON-LD BlogPosting items found!")
    else:
        LOGGER.debug("More than one JSON-LD BlogPosting item found!")

    webpagelist = [
        x
        for x in json_ld_dictlist
        if "@type" in x
        and (
            (isinstance(x["@type"], str) and x["@type"] in WEBPAGE_SCHEMA)
            or (isinstance(x["@type"], list) and x["@type"][0] in WEBPAGE_SCHEMA)
        )
    ]
    if len(webpagelist) == 1:
        sorted_article_dictlist.append(webpagelist[0])
    elif len(webpagelist) == 0:
        LOGGER.debug("No JSON-LD WebPage items found!")
    else:
        LOGGER.debug("More than one JSON-LD WebPage item found!")

    metadata_json_ld = {}
    metadata_json_ld["articleSection"] = []
    metadata_json_ld["author"] = []
    metadata_json_ld["image"] = []
    metadata_json_ld["keywords"] = []
    metadata_json_ld["publisher"] = []
    for item in sorted_article_dictlist:
        for prop in [
            "headline",
            "name",
            "articleBody",
            "articleSection",
            "description",
            "inLanguage",
            "datePublished",
            "dateModified",
            "dateCreated",
            "url",
            "author",
            "publisher",
            "image",
            "keywords",
        ]:
            # https://en.wikipedia.org/wiki/IETF_language_tag#:~:text=An%20IETF%20BCP%2047%20language,Taiwan%20using%20traditional%20Han%20characters.
            value = item.get(prop)
            if value is not None:
                if prop in ["author", "publisher"]:
                    if isinstance(value, dict):
                        org_name = value.get("name")
                        if org_name is not None and isinstance(org_name, str):
                            org_name = org_name.strip()
                            if len(org_name) > 0:
                                org_url = value.get("url")
                                if org_url is not None and isinstance(org_url, str):
                                    if len(org_url) > 0 and validate_url(org_url):
                                        pass
                                    else:
                                        org_url = None
                                metadata_json_ld[prop].append(
                                    {
                                        "name": org_name,
                                        "url": org_url,  # can be None
                                    }
                                )
                    else:
                        LOGGER.debug(
                            "JSON-LD dict: {} key had value not of instance dict.".format(prop)
                        )
                elif prop in ["image"]:
                    if isinstance(value, dict):
                        if value.get("@type") == "ImageObject":
                            url = value.get("url")
                            if validate_url(url):
                                metadata_json_ld[prop].append(url)
                    elif isinstance(value, list):
                        for image_item in value:
                            if isinstance(image_item, dict):
                                if image_item.get("@type") == "ImageObject":
                                    url = image_item.get("url")
                                    if validate_url(url):
                                        metadata_json_ld[prop].append(url)
                    else:
                        LOGGER.debug(
                            "JSON-LD dict: {} key had value not of instance dict or list.".format(
                                prop
                            )
                        )
                elif prop in ["articleSection"]:
                    if isinstance(value, str):
                        value = value.strip()
                        if len(value) > 0:
                            metadata_json_ld[prop].append(value)
                    elif isinstance(value, list):
                        for section in value:
                            if isinstance(section, str):
                                section = section.strip()
                                if len(section) > 0:
                                    metadata_json_ld[prop].append(section)
                    else:
                        LOGGER.debug(
                            "JSON-LD dict: {} key had value not of instance str or list.".format(
                                prop
                            )
                        )
                elif isinstance(value, str):
                    value = value.strip()
                    if len(value) > 0:
                        if prop == "keywords":
                            taglist = value.split(",")
                            taglist = [x.strip() for x in taglist]
                            taglist = [x for x in taglist if len(x) > 0]
                            metadata_json_ld[prop].extend(taglist)
                        else:
                            if prop in ["datePublished", "dateModified", "dateCreated"]:
                                value = parse_dt_str(value)
                            elif prop == "url":
                                if not validate_url(value):
                                    continue
                            if prop not in metadata_json_ld:
                                metadata_json_ld[prop] = value
                else:
                    LOGGER.debug("JSON-LD dict: {} key not recognized.".format(prop))

    return metadata_json_ld


def extract_metadata(
    soup: bs4.BeautifulSoup,
    uuid: str = None,
) -> dict[str, dict[str, Any]]:
    """Wrapper function around all metadata extraction functions.

    Written February 2021.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        The `bs4.BeautifulSoup` object representing the HTML document.
    uuid : str, optional
        An identifier of the HTML document, for external use.

    Returns
    -------
    metadata : dict[str, dict[str, Any]]
        A dict with the following key-value pairs:
        "json_ld" : metadata_json_ld
            The JSON-LD metadata as returned by `extract_json_ld().`
        "opengraph" : metadata_opengraph
            The OGP metadata as returned by `extract_opengraph()`.
    """
    metadata = {}
    metadata["json_ld"] = extract_json_ld(soup, uuid)
    LOGGER.debug("Collected JSON-LD metadata.")
    metadata["opengraph"] = extract_opengraph(soup, uuid)
    LOGGER.debug("Collected OpenGraph Protocol metadata.")
    return metadata
