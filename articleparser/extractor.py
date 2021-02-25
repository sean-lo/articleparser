"""Content identification and extraction module.

This module contains two classes: the `AssetExtractor` class which contains
routines regarding extraction of images, videos, links etc., and the 
`ArticleExtractor` subclass which contains routines extracting content regarding
web articles (author, title, description, keywords, article text).

Written February 2021.
"""

# Python 3.7 onwards, for annotations with standard collections
from __future__ import annotations

from collections import defaultdict, Counter, namedtuple
import copy
import difflib
import logging
import re
from typing import Any, Optional
import unicodedata
from urllib.parse import urljoin, urlparse, parse_qs

import bs4
import language_tags

from articleparser.config import Config
from articleparser.metadata import extract_metadata
from articleparser.settings import (
    IFRAME_SRC_ASSETS,
    IFRAME_SRC_IGNORELIST,
    IFRAME_SRCPARSE_IGNORELIST,
    LEFT_NOSPACE_PUNCTUATION,
    RIGHT_NOSPACE_PUNCTUATION,
)
from articleparser.util import (
    extend_config,
    get_child_text,
    get_css_selector_of_soup_tag,
    parse_dt_str,
    validate_url,
)

LOGGER = logging.getLogger(__name__)


class AssetExtractor(object):
    """Extracts assets from `bs4.BeautifulSoup` objects.

    An asset is an image, video, or other types of embedded content.
    We extract images via `get_pictures()`, and videos and others
    (external links, comment areas) via `get_assets()`.

    Written February 2021.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        The HTML document.
    page_url : str, optional
        The page URL of the article, or None if not provided.

    Attributes
    ----------
    soup
    page_url
    base_tag : bs4.element.Tag
        A `bs4.element.Tag` object representing the main section of the HTML
        document, from which all content and media are extracted.
    video_list : list[dict[str, Optional[str]]]
        A list of videos found from `base_tag`.
    links_list : list[dict[str, Optional[str]]]
        A list of external links found from `base_tag`.
        Contains the following keys:
        "url" : str
            The URL of the external link. This could be a link to an embedded Tweet.
        "text" : str or None
            The text of the link.
    comment_area_list : list[dict[str, Optional[str]]]
        A list of links to comment areas found from `base_tag`.
        Contains the following keys:
        "url" : str
            The URL of the embedded comment area.
        "text" : str or None
            The text of the comment area.
    image_list : list[dict[str, Optional[str]]]
        A list of images found from `base_tag`.
        Contains the following keys:
        "src" : str
            The URL of the image.
        "alt" : str or None
            The caption or alternate text of the image.
    document_list : list[dict[str, Optional[str]]]
        A list of documents found from `base_tag`.
        Contains the following keys:
        "url" : str
            The URL of the document. This has a path ending in ".pdf".
        "text" : str or None
            The text of the hyperlink linking to the document.

    Methods
    -------
    get_assets()
        Finds tags from `ASSET_TAGS` and processes them.
    get_documents()
        Gets all hyperlinks to documents in HTML.
    get_pictures()
        Gets images from `self.soup` and stores them in `self.image_list`.
    set_base_tag()
        Sets the base tag from which to extract assets.

    See Also
    --------
    ArticleExtractor : subclass including routines extracting article content.
    """

    URL_SCHEMES = [
        "http",
        "https",
        "",
    ]
    ASSET_TAGS = [
        # Image and multimedia
        "video",
        # Embedded content
        "embed",
        "iframe",
        "object",
    ]

    PICTURE_TAGS = [
        "figure",
        "picture",
        "img",
    ]
    # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types
    # collated Nov 2020
    IMAGE_MIME_TYPES = [
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types#WebP
        "image/webp",  # .webp
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types#JPEG
        "image/jpeg",  # .jpg, .jpeg, .jpe, .jif, .jfif
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types#PNG
        "image/png",  # .png
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types#GIF
        "image/gif",  # .gif
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types#AVIF
        "image/avif",  # .avif
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types#APNG
        "image/apng",  # .apng
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types#SVG
        # not included because likely to be for icons
        # "image/svg+xml", # .svg
        # (outdated)
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types#BMP
        # "image/bmp", # .bmp
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Image_types#TIFF
        # "image/tiff", # .tif, .tiff
    ]
    IMAGE_MIME_SUFFIXES = [
        ".webp",
        ".jpg",
        ".jpeg",
        ".jpe",
        ".jif",
        ".jfif",
        ".png",
        ".gif",
        ".avif",
        ".apng",
    ]

    # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers
    # collated Nov 2020
    VIDEO_MIME_TYPES = [
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#MP4
        "video/mp4",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#Ogg
        "video/ogg",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#WebM
        "video/webm",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#QuickTime
        "video/quicktime",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#3GP
        "video/3gpp",
        "video/3gpp2",
        "video/3gp2",
    ]

    # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers
    # collated Nov 2020
    AUDIO_MIME_TYPES = [
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#MPEG
        "audio/mp3",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#MP4
        "audio/mp4",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#ADTS
        "audio/mpeg",
        "audio/aac",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#FLAC
        "audio/flac",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#WAVE
        "audio/wave",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#Ogg
        "audio/ogg",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#WebM
        "audio/webm",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#3GP
        "audio/3gpp",
        "audio/3gpp2",
        "audio/3gp2",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#WAVE
        "audio/wav",
        "audio/x-wav",
        "audio/x-pn-wav",
        # https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Containers#FLAC
        "audio/x-flac",
    ]

    def __init__(
        self,
        soup: bs4.BeautifulSoup,
        page_url: str = None,
    ):
        self.soup = soup
        self.page_url = page_url
        self.base_tag = None
        self.video_list = []
        self.links_list = []
        self.comment_area_list = []
        self.image_list = []
        self.document_list = []

    @staticmethod
    def _make_video_item(
        tag_name: str,
        height: str,  # need not be a number, e.g. "100%"
        width: str,  # need not be a number, e.g. "100%"
        src: str,
        page_url: str,
        mime_type: str = None,
    ) -> dict[str, Optional[str]]:
        """Makes a video item to add to `self.video_list`.

        Written December 2020.

        Parameters
        ----------
        tag_name: str
            The name of the tag containing the video.
        height : str or None
            The value of the `height` HTML attribute of the tag. Need not be a
            number, e.g. "100%".
        width : str or None
            The value of the `width` HTML attribute of the tag. Need not be a
            number, e.g. "100%".
        src : str
            The source URL of the video, a required attribute.
        page_url : str
            The page URL the video is from (equal to `self.page_url`).
        mime_type : str, optional
            The MIME type of the tag. Not provided if `tag_name="iframe"`.

        Returns
        -------
        A dictionary with the above key-value pairs, and:
        video_url : str
            The computed video URL of the video as returned by `urljoin()`.
        video_netloc : str
            The network location of `video_url` as returned by `urlparse()`.
        """
        video_url = urljoin(page_url, src)
        video = {
            "tag_name": tag_name,
            "height": height,
            "width": width,
            "src": src,
            "page_url": page_url,
            "mime_type": mime_type,
            "video_url": video_url,
            "video_netloc": urlparse(video_url).netloc,
        }
        return video

    def _process_iframe_tag(
        self,
        tag: bs4.element.Tag,
    ) -> None:
        """Processes `<iframe>` tag according to its `src` attribute.

        Checks if `src` attribute exists. If it does, and if its network
        location (according to `urlparse()`) is in a recognized list
        `IFRAME_SRC_ASSETS`, process it using `_process_platform_iframe_tag()`.

        If not in this list, and if its path and netloc matches that as found
        in `IFRAME_SRCPARSE_IGNORELIST`, do nothing; otherwise, record the `src`
        using `_write_src_to_log()`.

        Written December 2020.

        Parameters
        ----------
        tag: bs4.element.Tag
            The `<iframe>` tag to process.

        Returns
        -------
        None
        """
        assert tag.name == "iframe"
        src = tag.get("src")
        if src is None or src == "":
            # contents of <iframe> likely dynamically inserted by <script> - likely to be ads
            return
        if src in IFRAME_SRC_IGNORELIST:
            return

        src_parse = urlparse(src)
        for platform in IFRAME_SRC_ASSETS:
            if platform in src_parse.netloc:
                self._process_platform_iframe_tag(tag, platform)
                return
        else:
            # platform not found in IFRAME_SRC_ASSETS
            for ignore_netloc, ignore_path in IFRAME_SRCPARSE_IGNORELIST:
                if re.fullmatch(ignore_netloc, src_parse.netloc):
                    if re.fullmatch(ignore_path, src_parse.path):
                        # ignore this URL
                        return
            else:
                self._write_src_to_log(src, "netloc", "_process_iframe_tag")
                return

    def _process_platform_iframe_tag(
        self,
        tag: bs4.element.Tag,
        platform: str,
    ) -> None:
        """Processes `<iframe>` tag according to the netloc of its `src`.

        According to the behaviour of `IFRAME_SRC_ASSETS`, classify `src` as
        belonging in one of these categories:
        - "video": appends it to `self.video_list`;
        - "comments": appends it to `self.comment_area_list`;
        - "links": appends it to `self.links_list`;
        - "ignore": does nothing.

        If `src` does not match any expression in `IFRAME_SRC_ASSETS`, record it
        in a log file using `_write_src_to_log()`.

        If not in this list, and if its path and netloc matches that as found
        in `IFRAME_SRCPARSE_IGNORELIST`, do nothing; otherwise, record the `src`
        using `_write_src_to_log()`.

        Written December 2020.

        Parameters
        ----------
        tag: bs4.element.Tag
            The `<iframe>` tag to process.

        Returns
        -------
        None
        """
        assert tag.name == "iframe"
        assert platform in IFRAME_SRC_ASSETS
        src = tag.get("src")
        if not src:
            return
        src_parse = urlparse(src)
        for netloc_r, path_r_dict in IFRAME_SRC_ASSETS[platform].items():
            if re.fullmatch(netloc_r, src_parse.netloc):
                for path_r, category in path_r_dict.items():
                    if re.fullmatch(path_r, src_parse.path):
                        assert category in ["video", "comments", "links", "ignore"]
                        if category == "video":
                            video = self._make_video_item(
                                tag_name="iframe",
                                height=tag.get("height"),
                                width=tag.get("width"),
                                src=src,
                                page_url=self.page_url,
                            )
                            self.video_list.append(video)
                            return
                        elif category == "comments":
                            self.comment_area_list.append(
                                {
                                    "url": src,
                                    "text": None,
                                }
                            )
                            return
                        elif category == "links":
                            self.links_list.append(
                                {
                                    "url": src,
                                    "text": None,
                                }
                            )
                            return
                        elif category == "ignore":
                            return
                else:
                    # src_parse.path did not match any known pattern
                    self._write_src_to_log(src, "path", "_process_platform_iframe_tag")
                    return

        else:
            # src_parse.netloc did not match any known pattern
            self._write_src_to_log(src, "netloc", "_process_platform_iframe_tag")
            return

    def _write_src_to_log(self, src: str, error_type: str, func: str) -> None:
        """Write unrecognized `src` attributes in `<iframe>` to a log file.

        Written February 2021.

        Parameters
        ----------
        src: str
            The unrecognized URL.
        error_type: {"netloc", "path"}
            The URL component unrecognized.
        func: {"_process_iframe_tag", "_process_platform_iframe_tag"}
            The parent method calling this method.

        Returns
        -------
        None
        """
        assert error_type in ["netloc", "path"]
        assert func in ["_process_iframe_tag", "_process_platform_iframe_tag"]
        message_list = [
            "From function: {:<28}".format(func),
            "Unrecognized {:<6} of <iframe> URL: {}".format(error_type, src),
            "Article URL: {}".format(self.page_url),
        ]
        message = " - ".join(message_list)
        LOGGER.debug(message.encode("utf-8"))
        return

    def _process_video_tag(
        self,
        tag: bs4.element.Tag,
    ) -> None:
        """Processes content in `<video>` tags.

        The `<video>` tag can either have a link to the content in its `src`
        attribute, or contain `<source>` children tag(s) containing it.

        `Specification <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/video>`_

        Written December 2020.

        Parameters
        ----------
        tag: bs4.element.Tag
            The `<video>` tag to process.

        Returns
        -------
        None
        """
        assert tag.name == "video"
        src = tag.get("src")  # optional
        height = tag.get("height")
        width = tag.get("width")

        if src:
            video = self._make_video_item(
                tag_name="video",
                height=height,
                width=width,
                src=src,
                page_url=self.page_url,
            )  # TODO: src may be a blob: type URL, requires further processing
            self.video_list.append(video)
            return
        else:
            # source of video is in child <source> tags
            # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/source
            source_list = list(tag.find_all("source"))
            if not source_list:
                LOGGER.debug("Did not find any <source> tag in <video>.")
                return
            for source_tag in source_list:
                if source_tag.get("type") not in self.VIDEO_MIME_TYPES:
                    LOGGER.debug(
                        "Unrecognized video format in <source> in <video>: {}".format(
                            source_tag.get("type")
                        )
                    )

            # iterable defines preference of MIME types for multiple <source> tags in <video>
            for mime_type in self.VIDEO_MIME_TYPES:
                for source_tag in source_list:
                    if source_tag.get("type") == mime_type:
                        self.video_list.append(
                            self._make_video_item(
                                tag_name="video",
                                height=height,
                                width=width,
                                src=source_tag.get("src"),  # required attribute
                                page_url=self.page_url,
                                mime_type=mime_type,
                            )
                        )
                        return

            return

    def _process_embed_tag(
        self,
        tag: bs4.element.Tag,
    ) -> None:
        """Processes content in `<embed>` tags.

        The content is categorized according to the MIME type (stored in the
        `type` attribute).

        `Specification <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/embed>`_

        Written December 2020.

        Parameters
        ----------
        tag: bs4.element.Tag
            The `<embed>` tag to process.

        Returns
        -------
        None
        """
        assert tag.name == "embed"
        # empty element - cannot contain anything
        src = tag.get("src")  # required
        # list of MIME types:
        # https://www.iana.org/assignments/media-types/media-types.xhtml
        mime_type = tag.get("type")
        if not mime_type:
            return
        if mime_type.startswith("video"):
            video = self._make_video_item(
                tag_name="embed",
                height=tag.get("height"),
                width=tag.get("width"),
                src=src,
                page_url=self.page_url,
                mime_type=mime_type,
            )
            self.video_list.append(video)
            return
        elif mime_type.startswith("application"):
            # TODO: find which MIME types can be used as video formats
            return
        else:
            return

    def _process_object_tag(
        self,
        tag: bs4.element.Tag,
    ) -> None:
        """Processes content in `<object>` tag.

        `Specification <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/object>`_

        The content (URL in the `data` attribute) is categorized according to
        the MIME type (stored in the `type` attribute).

        Written December 2020.

        Parameters
        ----------
        tag: bs4.element.Tag
            The `<object>` tag to process.

        Returns
        -------
        None
        """
        data = tag.get("data")
        mime_type = tag.get("type")
        if not mime_type:
            return
        if mime_type.startswith("video"):
            video = self._make_video_item(
                tag_name="object",
                height=tag.get("height"),
                width=tag.get("width"),
                src=data,
                page_url=self.page_url,
                mime_type=mime_type,
            )
            self.video_list.append(video)
            return
        elif mime_type.startswith("application"):
            # TODO: find which MIME types can be used as video formats
            return
        else:
            return

    def get_assets(self) -> None:
        """Finds tags from `ASSET_TAGS` and processes them.

        Wrapper function to perform different actions on different tags that
        could potentially contain assets, as listed in `ASSET_TAGS`.
        If `base_tag` is not set, call `set_base_tag()` first.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if not self.base_tag:
            self.set_base_tag()
        for iframe in self.base_tag.find_all("iframe"):
            self._process_iframe_tag(iframe)
        for video in self.base_tag.find_all("video"):
            self._process_video_tag(video)
        for embed in self.base_tag.find_all("embed"):
            self._process_embed_tag(embed)
        for obj in self.base_tag.find_all("object"):
            self._process_object_tag(obj)

        self.links_list = self._process_link_list(self.links_list)
        self.comment_area_list = self._process_link_list(self.comment_area_list)

        return

    def get_documents(self) -> None:
        """Gets all hyperlinks to documents in HTML.

        Retrieves all anchor tags that have a "href" attribute pointing to
        a URL with a path ending in ".pdf". Stores the result in
        `self.document_list`.

        If `base_tag` is not set, call `set_base_tag()` first.

        Written February 2021.

        Parameters
        ----------
        None

        Returns
        -------
        None

        """
        if not self.base_tag:
            self.set_base_tag()

        for anchor in self.base_tag.find_all("a"):
            text = anchor.get_text()
            href = anchor.get("href")
            if href:
                # detects URL paths ending with ".pdf" suffix
                if urlparse(href).path.lower().endswith(".pdf"):
                    self.document_list.append(
                        {
                            "url": href,
                            "text": text,
                        }
                    )

        self.document_list = self._process_link_list(self.document_list)

        return

    def _process_link_list(
        self,
        link_list: list[dict[str, Optional[str]]],
    ) -> list[dict[str, Optional[str]]]:
        """Processes a list of link objects.

        Removes links that:
        - begin with "#" (relative links);
        - have a URL scheme not in {"http", "https", ""};

        Thereafter, performs `urljoin` on `self.page_url` and the `url` of the
        link object.

        Written January 2021.

        Parameters
        ----------
        link_list : list[dict[str, Optional[str]]]
            A list of link objects (represented as dicts), each with the link
            following key-value pairs:
            "url" : str or None
                The URL of the link object.
            "text" : str or None
                The text of the link object.

        Returns
        -------
        processed_link_list : list[dict[str, Optional[str]]]
            The processed link list.
        """

        processed_link_list = []
        for link_item in link_list:
            href = link_item.get("url")
            if not href:
                continue
            href = href.strip()
            if href.startswith("#"):
                # linking to HTML element on same page; ignore
                continue
            href_parse = urlparse(href)
            if href_parse.scheme not in self.URL_SCHEMES:
                continue

            processed_href = urljoin(self.page_url, href)
            text = link_item.get("text")
            if text:
                processed_text = text.strip()
            else:
                processed_text = None

            processed_link_list.append(
                {
                    "url": processed_href,
                    "text": processed_text,
                }
            )
        return processed_link_list

    @staticmethod
    def _parse_media_string(media: str) -> (Optional[int], Optional[int]):
        """Parse `media` attribute of <source> tags in <picture>.

        The `media` attribute follows the `syntax
        <https://developer.mozilla.org/en-US/docs/Web/CSS/Media_Queries/Using_media_queries>`_

        We only consider the media features `min-width` and `max-width`
        and return a tuple of these features.

        Written December 2020.

        Parameters
        ----------
        media : str
            The `media` attribute.

        Returns
        -------
        min_width: int or None
            The minimum width media feature, or None.
        max_width: int or None
            The maximum width media feature, or None.
        """
        min_pixels = None
        max_pixels = None
        if not media:
            return (min_pixels, max_pixels)

        MEDIA_MINWIDTH_REGEX = re.compile(
            r"""
                \(
                min-width:\s*
                (\d+)px
                \)
            """,
            flags=re.VERBOSE,
        )
        MEDIA_MAXWIDTH_REGEX = re.compile(
            r"""
                \(
                max-width:\s*
                (\d+)px
                \)
            """,
            flags=re.VERBOSE,
        )

        min_match = re.search(MEDIA_MINWIDTH_REGEX, media)
        if min_match:
            min_pixels = int(min_match.group(1))
        max_match = re.search(MEDIA_MAXWIDTH_REGEX, media)
        if max_match:
            max_pixels = int(max_match.group(1))
        return (min_pixels, max_pixels)

    @staticmethod
    def _parse_srcset_string(srcset: str) -> dict[str, list[float, str]]:
        """Parses a `srcset` attribute string from <source> or <img> tags.

        Specification:
        `source <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/source#attr-srcset>`_
        `img <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img#attr-srcset`_

        Written December 2020.

        Parameters
        ----------
        srcset : str
            The `srcset` attribute string.

        Returns
        -------
        srcset_dict : dict
            A dict with the following keys and values:
            "w" : list[int, str]
                A (possibly empty) list of tuples (int, str),
                where the first entry is the width descriptor,
                 where the first entry is the width descriptor,
                where the first entry is the width descriptor,
                 where the first entry is the width descriptor,
                where the first entry is the width descriptor,
                and the second entry is the URL.
            "x" : list[float, str]
                A (possibly empty) list of tuples (float, str),
                where the first entry is the pixel density descriptor,
                and the second entry is the URL.
        """
        # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/source#attr-srcset
        # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img#attr-srcset=
        srcset_dict = {
            "w": [],
            "x": [],
        }
        if not srcset:
            return srcset_dict

        # Split by: comma, then one or more whitespace
        # comma alone insufficient, because
        # comma without whitespace can occur in URLs
        src_list = re.split(r",\s+", srcset)
        for src_str in src_list:
            src_str = src_str.strip()  # remove trailing and leading whitespace
            if not src_str:
                continue
            src_item_list = src_str.split()  # space-separated
            if len(src_item_list) == 2:
                modifier = src_item_list[1]
                amt, modifier = modifier[:-1], modifier[-1]
                if modifier == "x":
                    srcset_dict["x"].append((float(amt), src_item_list[0]))
                elif modifier == "w":
                    srcset_dict["w"].append((int(amt), src_item_list[0]))
            elif len(src_item_list) == 1:
                # the srcset can end with a trailing comma without whitespace
                # deal with last trailing comma w/o whitespace
                if src_item_list[0].endswith(","):
                    src_item_list[0] = src_item_list[0][:-1]
                srcset_dict["x"].append((1.0, src_item_list[0]))
        return srcset_dict

    @staticmethod
    def _get_best_src_from_srcset_dict(in_srcset_dict: dict) -> Optional[str]:
        """Gets best image URL from `srcset` of <img> or <picture> tag.

        The image URLs are selected according to the following priority:
        - The URL corresponding to the largest width descriptor;
        - The URL corresponding to the largest pixel density descriptor.

        Written December 2020.

        Parameters
        ----------
        in_srcset_dict: dict
            The dict representing the `srcset`, as returned by
                The dict representing the `srcset`, as returned by
            The dict representing the `srcset`, as returned by
                The dict representing the `srcset`, as returned by
            The dict representing the `srcset`, as returned by
            `_parse_srcset_string()`.

        Returns
        -------
        str or None
            A string of the 'best' image URL selected.
            `None` is returned if the input was empty; that is,
            `{"w": [], "x": []}`.
        """
        srcset_dict = in_srcset_dict.copy()

        # sort items in "w" and "x" keys according to descriptor amount,
        # in descending order
        srcset_dict["w"].sort(key=lambda x: x[0], reverse=True)
        srcset_dict["x"].sort(key=lambda x: x[0], reverse=True)
        # prioiritize returning larger images
        if len(srcset_dict["w"]) > 0:
            return srcset_dict["w"][0][1]
        else:
            # secondly, prioritize returning higher-resolution images
            if len(srcset_dict["x"]) > 0:
                return srcset_dict["x"][0][1]
            else:
                return None

    @classmethod
    def _process_sources_in_picture_tag(
        cls,
        tag: bs4.element.Tag,
    ) -> dict[str, Optional[str]]:
        """Gets best image URL from <source> tags in <picture>.

        The <picture> tag contains "zero or more <source> elements and one
        <img> element, offering alternative versions of an image for
        different display/device scenarios". This method combines all URLs
        from these <source> tags, and chooses the image to return according
        to the following:
        - the <type> element matching the priority as listed in
          `cls.IMAGE_MIME_TYPES`;
        - the image intended for the largest display width as determined by
          the `media` attribute;
        - the largest resolution image from that `srcset` attribute of the
          <source> tag, as computed by `_get_best_src_from_srcset_dict()`.

        Written December 2020.

        Parameters
        ----------
        tag : bs4.element.Tag
            The <picture> tag to analyze.
            `Specification <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/picture>`_

        Returns
        -------
        dict[str, Optional[str]]
            A dict with key "source_src" and value the URL of the image;
            this URL can be a relative URL, or possibly a data URL
            (starting with "data:")
            Value is `None` if there are no <source> tags in <picture> with
            MIME type unspecified or belonging in `cls.IMAGE_MIME_TYPES`.
        """
        assert tag.name == "picture"
        source_list = tag.find_all("source", recursive=False)
        if len(source_list) == 0:
            return {"source_src": None}

        ### Collecting info from <source> tags ###
        sources_dict = {}
        Source = namedtuple("Source", ["mime_type", "min_pixels", "max_pixels"])
        for source in tag.find_all("source", recursive=False):
            # srcset: required attribute
            source_srcset = source.get("srcset")
            # data-srcset: commonly seen alternative / complement;
            source_datasrcset = source.get("data-srcset")
            source_srcset_dict = cls._parse_srcset_string(source_srcset)
            source_datasrcset_dict = cls._parse_srcset_string(source_datasrcset)
            source_srcset_dict["w"].extend(source_datasrcset_dict["w"])
            source_srcset_dict["x"].extend(source_datasrcset_dict["x"])
            if source_srcset_dict == {"w": [], "x": []}:
                # both srcset and data-srcset are None
                continue

            # media: media queries for the source tag, if any
            source_media = source.get("media")
            source_media_tuple = cls._parse_media_string(source_media)

            # use a namedtuple of MIME type and media tuple to record the sources
            source_desc = Source(
                source.get("type"),  # MIME type of source tag (optional)
                source_media_tuple[0],
                source_media_tuple[1],
            )

            if source_desc not in sources_dict:
                sources_dict[source_desc] = {
                    "srcset_dict": source_srcset_dict,
                }
            else:
                # for when multiple source tags have the same mime type and media query
                sources_dict[source_desc]["srcset_dict"]["w"].extend(source_srcset_dict["w"])
                sources_dict[source_desc]["srcset_dict"]["x"].extend(source_srcset_dict["x"])

        ### Processing each <source> tag: ###
        ### removing dupes, then getting "best" src for each tag ###
        for source_desc, source_dict in sources_dict.items():
            # remove duplicates
            source_dict["srcset_dict"]["w"] = list(set(source_dict["srcset_dict"]["w"]))
            source_dict["srcset_dict"]["x"] = list(set(source_dict["srcset_dict"]["x"]))
            # remove items that have "too small widths"
            source_dict["srcset_dict"]["w"] = [
                item for item in source_dict["srcset_dict"]["w"] if item[0] > 1
            ]
            # interpret srcset_dict and get result
            source_dict["best_src"] = cls._get_best_src_from_srcset_dict(
                source_dict["srcset_dict"],
            )

        ### Comparing the 'media' and 'type' attributes of <source> tags ###
        ### to determine the 'best' to return ###

        if len(sources_dict) == 0:
            return {"source_src": None}

        # filter out undesired image MIME types
        sources_dict = {
            desc: item
            for desc, item in sources_dict.items()
            if desc.mime_type is None  # allow for unspecified MIME type
            or desc.mime_type in cls.IMAGE_MIME_TYPES
        }

        if len(sources_dict) == 0:
            return {"source_src": None}

        # select best source to return based on priority in IMAGE_MIME_TYPES
        for mime_type in cls.IMAGE_MIME_TYPES + [None]:
            filtered_sources_dict = {
                desc: item for desc, item in sources_dict.items() if desc.mime_type == mime_type
            }
            if filtered_sources_dict:
                if len(filtered_sources_dict) == 1:
                    desc, item = filtered_sources_dict.popitem()
                    best_src = item["best_src"]
                    if best_src:
                        return {"source_src": best_src}
                else:
                    # choose the source item with the largest media query
                    # choose the source item with the largest min_pixels
                    min_pixels_sources_dict = {
                        desc: item
                        for desc, item in filtered_sources_dict.items()
                        if desc.min_pixels is not None
                    }
                    if min_pixels_sources_dict:
                        desc = max(min_pixels_sources_dict, key=lambda x: x.min_pixels)
                        best_src = min_pixels_sources_dict[desc]["best_src"]
                        if best_src:
                            return {"source_src": best_src}
                    # else, choose the source item with the largest max_pixels
                    max_pixels_sources_dict = {
                        desc: item
                        for desc, item in filtered_sources_dict.items()
                        if desc.max_pixels is not None
                    }
                    if max_pixels_sources_dict:
                        desc = max(max_pixels_sources_dict, key=lambda x: x.max_pixels)
                        best_src = max_pixels_sources_dict[desc]["best_src"]
                        if best_src:
                            return {"source_src": best_src}

    @classmethod
    def _check_image_mime_type(
        cls,
        src: str,
    ) -> bool:
        """Checks if `src` has a suffix corresponding to an image MIME type.

        The suffixes allowed are listed in `cls.IMAGE_MIME_SUFFIXES`.

        Written February 2021.

        Parameters
        ----------
        src : str
            The URL to check.

        Returns
        -------
        bool
            Whether this URL corresponds to an image MIME type.
        """
        src_parse = urlparse(src)
        query_obj = parse_qs(src_parse.query)
        src = None
        if query_obj.get("src"):
            src = query_obj.get("src")[0]

        for mime_type in cls.IMAGE_MIME_SUFFIXES:
            if src_parse.path.lower().endswith(mime_type):
                return True
            elif src:
                if src.lower().endswith(mime_type):
                    return True
        return False

    @classmethod
    def _process_img_tag(
        cls,
        tag: bs4.element.Tag,
    ) -> dict[str, Optional[str]]:
        """Gets image info from <img> tag.

        `Specification <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/img>`_

        The image URL is obtained according to the following priority:
        - from the `srcset` attribute, if present;
          the `srcset` attribute is parsed by `_parse_srcset_string()`
          and the URL is selected by `_get_best_src_from_srcset_dict()`.
            - items with too-small width descriptor values are removed
        - from the `data-src` attribute, if present;
          though not standard HTML, it occurs often enough such that
              though not standard HTML, it occurs often enough such that
          though not standard HTML, it occurs often enough such that
              though not standard HTML, it occurs often enough such that
          though not standard HTML, it occurs often enough such that
          the fallback to `src` attribute usually indicates an error and
          the `src` attribute therefore holds an exception image.
        - from the `src` attribute; this is a required attribute of the
          <img> tag.

        Written December 2020.

        Parameters
        ----------
        tag : bs4.element.Tag
            The <img> tag.

        Returns
        -------
        img_dict : dict
            A dict with the following key-value pairs:
            "img_src" : str
                The image URL.
            "img_alt" : str or None
                The image alternate text from the `alt` attribute.
                `None` if `tag` does not have a `alt` attribute (or if its `alt`
                attribute is fully whitespace).
            Both values are `None` if `tag` is `None`, or if `tag` does not have
            a `data-src` attribute or `src` attribute.
        """
        if tag is None:
            return {"img_src": None, "img_alt": None}

        assert tag.name == "img"
        # if <img> tag has "srcset" attribute, use it
        img_srcset = tag.get("srcset")
        if img_srcset:
            # https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images
            img_srcset_dict = cls._parse_srcset_string(img_srcset)
            # remove items that have too small widths
            img_srcset_dict["w"] = [item for item in img_srcset_dict["w"] if item[0] > 1]
            img_src = cls._get_best_src_from_srcset_dict(img_srcset_dict)
        # otherwise, default to "src" attribute
        else:
            # not required, but if present, more reliable
            img_src = tag.get("data-src")
            if (not img_src) or (not cls._check_image_mime_type(img_src)):
                # fallback, but some malformed tags do not have this
                img_src = tag.get("src")
                if (not img_src) or (not cls._check_image_mime_type(img_src)):
                    return {"img_src": None, "img_alt": None}

        # get alt text from image
        img_alt = tag.get("alt")
        if img_alt:
            img_alt = img_alt.strip()
            if img_alt == "":
                img_alt = None
        return {"img_src": img_src, "img_alt": img_alt}

    @classmethod
    def _process_picture_tag(
        cls,
        tag: bs4.element.Tag,
    ) -> dict[str, Optional[str]]:
        """Get information from <picture> tag.

        `Specification <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/picture>`_

        This method calls `_process_sources_in_picture_tag()` to parse the
        <source> tags that are direct children. It then calls
        `_process_img_tag()` to parse the <img> tag in <picture>
        (there is exactly one such tag).

        Written December 2020.

        Parameters
        ----------
        tag : bs4.element.Tag
            The <picture> tag.

        Returns
        -------
        picture_dict : dict
            A dict with the following key-value pairs:
            "img_src" : str or None
                The image URL, as returned by `_process_img_tag()`.
            "img_alt" : str or None
                The image alternate text from the `alt` attribute,
                as returned by `_process_img_tag()`.
            "source_src" : str or None
                The image URL, as returned by
                `_process_sources_in_picture_tag()`.
        """
        assert tag.name == "picture"
        # parse <source> children tags
        source_dict = cls._process_sources_in_picture_tag(tag)

        img = tag.find("img")  # each <picture> tag has an <img> tag
        img_dict = cls._process_img_tag(img)

        picture_dict = {**img_dict, **source_dict}

        return picture_dict

    @classmethod
    def _process_figure_tag(
        cls,
        tag: bs4.element.Tag,
    ) -> Optional[dict[str, Optional[str]]]:
        """Get information from <figure> tag.

        `Specification <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/figure>`_

        This method finds a <figcaption> child in <figure> (optional, if it
        exists only the first one is presented), and gets its text.

        This method finds a <picture> child, and processes it via
        `_process_picture_tag()` if it exists.

        Otherwise, it finds a <img> child and processes it via
        `_process_img_tag()` if it exists.

        Written December 2020.

        Parameters
        ----------
        tag : bs4.element.Tag
            The <figure> tag.

        Returns
        -------
        figure_dict : dict
            A dict with the following key-value pairs:
            "figcaption" : str or None
                The text contained in the <figcaption> element.
                `None` if `tag` has no <figcaption> descendant,
                or if <figcaption> descendant contains no text,
                or text that is fully whitespace.
            "img_src" : str or None
                The image URL, as returned by `_process_img_tag()`.
            "img_alt" : str or None
                The image alternate text from the `alt` attribute,
                as returned by `_process_img_tag()`.
            "source_src" : str or None
                The image URL, as returned by
                `_process_sources_in_picture_tag()`.
                Not present if <picture> child was not found.
            `None` if `tag` has no <picure> or <img> descendant.
        """
        assert tag.name == "figure"
        figcaption = tag.find("figcaption")

        if figcaption:
            figcaption_text = figcaption.get_text().strip()
            if figcaption_text == "":
                figcaption_text = None
        else:
            figcaption_text = None

        contains_image = False
        picture = tag.find("picture")
        if picture:
            picture_dict = cls._process_picture_tag(picture)
            # checks if picture_dict has any non-None value
            if any(picture_dict.values()):
                contains_image = True
                figure_dict = picture_dict.copy()
                figure_dict["figcaption"] = figcaption_text
                return figure_dict

        if not contains_image:
            img = tag.find("img")
            if img:
                img_dict = cls._process_img_tag(img)
                if any(img_dict.values()):
                    contains_image = True
                    figure_dict = img_dict.copy()
                    figure_dict["figcaption"] = figcaption_text
                    return figure_dict

        if not contains_image:
            LOGGER.debug("No <picture> or <img> tag found in <figure>!")
            return None

    def get_pictures(self) -> None:
        """Gets images from `self.soup` and stores them in `self.image_list`.

        Searches within `soup.body` the following:
        - <figure> tags, processed with `_process_figure_tag()`;
        - <picture> tags not previously encountered,
          processed with `_process_picture_tag()`;
        - <img> tags not previously encountered,
          processed with `_process_img_tag()`;

        For each result, a dict is appended to `self.image_list`, with the
        following key-value pairs:
        "src" : the URL of the image;
            relative URLs are joined using `urljoin()` to `self.page_url`
        "alt" : the text describing the image.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if not self.base_tag:
            self.set_base_tag()

        # `<figure>` tags in soup.body
        for figure in self.base_tag.find_all("figure"):
            figure_dict = self._process_figure_tag(figure)
            if figure_dict:  # figure_dict could be None
                if any(figure_dict.values()):
                    self.image_list.append(
                        {
                            "src": (
                                figure_dict.get("source_src")
                                if figure_dict.get("source_src")
                                else figure_dict.get("img_src")
                            ),
                            "alt": (
                                figure_dict.get("figcaption")
                                if figure_dict.get("figcaption")
                                else figure_dict.get("img_alt")
                            ),
                        }
                    )
        # `<picture>` tags in soup.body
        for picture in self.base_tag.find_all("picture"):
            # exclude those already encountered as child of `<figure>`
            if not picture.find_parent("figure"):
                picture_dict = self._process_picture_tag(picture)
                if any(picture_dict.values()):
                    self.image_list.append(
                        {
                            "src": (
                                picture_dict.get("source_src")
                                if picture_dict.get("source_src")
                                else picture_dict.get("img_src")
                            ),
                            "alt": picture_dict.get("img_alt"),
                        }
                    )
        # `<img>` tags in soup.body
        for img in self.base_tag.find_all("img"):
            # exclude those already encountered as child of `<figure>`
            if not img.find_parent("figure"):
                # exclude those already encountered as child of `<picture>`
                if not img.find_parent("picture"):
                    img_dict = self._process_img_tag(img)
                    if any(img_dict.values()):
                        self.image_list.append(
                            {
                                "src": img_dict.get("img_src"),
                                "alt": img_dict.get("img_alt"),
                            }
                        )

        # Perform urljoin() to deal with relative image URLs
        for image_item in self.image_list:
            src = image_item.get("src")
            # deals with relative image URLs,
            # leaves absolute URLs or URLs starting with "data:" unchanged
            image_item["src"] = urljoin(self.page_url, src)

        return

    def set_base_tag(self) -> None:
        """Sets the base tag from which to extract assets.

        For the base `AssetExtractor` class, this is just `soup.body`.
        The `ArticleExtractor` subclass overwrites this method to select
        a descendant of `soup.body`, for more targeted asset extraction.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        None

        See Also
        --------
        ArticleExtractor.set_base_tag
        """
        # overridden in ArticleExtractor subclass
        self.base_tag = self.soup.body
        return


class ArticleExtractor(AssetExtractor):
    """Extracts content from `bs4.BeautifulSoup` objects representing articles.

    This class subclasses `AssetExtractor` and includes routines for extraction
    of "short fields" (such as authors, description, title) as well as article
    text. The section on extracting article text involves determining the "top
    tag" (in `set_top_tag()`) which is the most likely to contain text content.

    Written February 2021.

    Parameters
    ----------
    soup : bs4.BeautifulSoup
        The HTML document.
        Same as in AssetExtractor.
        Same as in AssetExtractor.
    metadata : dict[str, dict[str, Any]]
        The article metadata.
    config : articleparser.config.Config
        A Config object consisting optional settings.
    page_url : str, optional
        The page URL of the article, or None if not provided.
        Same as in AssetExtractor.

    Attributes
    ----------
    soup
    metadata
    config
    page_url
    base_tag : bs4.element.Tag
        A `bs4.element.Tag` object representing the main section of the HTML
        document, from which all content and media are extracted.
        Same as in AssetExtractor.
    top_tag : bs4.element.Tag
        A `bs4.element.Tag` object representing the section of the HTML document
        from which article text should be extracted.
    video_list : list[dict[str, Optional[str]]]
        A list of videos found from `base_tag`.
        Same as in AssetExtractor.
    links_list : list[dict[str, Optional[str]]]
        A list of external links found from `base_tag`.
        Same as in AssetExtractor.
    comment_area_list : list[dict[str, Optional[str]]]
        A list of links to comment areas found from `base_tag`.
        Same as in AssetExtractor.
    image_list : list[dict[str, Optional[str]]]
        A list of images found from `base_tag`.
        Same as in AssetExtractor.
    inline_links_list : list[dict[str, Optional[str]]]
        A list of inline links found from `base_tag`.
        Contains the following keys:
        "url" : str
            The URL of the anchor tag.
        "text" : str
            The text in the anchor tag.
    article_text: list[str]
        A list of strings each representing a paragraph extracted from `top_tag`.

    Methods
    -------
    extract_page_url()
        Extracts page URL from `self.soup`.
    extract_authors()
        Extracts authors from `self.soup`.
    extract_description()
        Extracts article description from `self.soup`.
    extract_language()
        Gets BCP47 language tag of HTML document.
    extract_keywords()
        Extracts article keywords from `self.soup`.
    extract_timestamps()
        Extracts timestamps from `self.soup`.
    extract_title(clean=True)
        Extracts article title from `self.soup`.
    set_base_tag()
        Sets the base tag from which to extract assets.
    set_top_tag()
        Sets the top tag, containing article text, in `self.top_tag`.
    remove_high_linkdensity_sections()
        Removes sections of high link-density from `self.top_tag`.
    get_article_text()
        Produces article text from a HTML document.

    See Also
    --------
    AssetExtractor : base class for asset extraction.
    """

    TAGS_TO_CHECK_LISTS = [  # Contains tags that "indicate" functions that find top tag
        ["p"],
        ["span", "ol", "ul"],
        ["div", "section"],
    ]
    TEXT_TO_COLLECT_LISTS = [
        # Tags to collect article text from within top_tag
        ["p", "li", "pre", "blockquote", "dt", "dd"],
        # Backup to collect article text from within top_tag
        ["p", "li", "pre", "blockquote", "dt", "dd", "span"],
        ["p", "li", "pre", "blockquote", "dt", "dd", "span", "div", "section"],
    ]
    BASE_TAG_SELECTORS = [  # CSS selectors that select base_tag
        # *= allows for substrings
        # (e.g. matching "http://..." and "https://...")
        (
            "article[itemtype*='schema.org/NewsArticle'], "
            "article[itemtype*='schema.org/Article'], "
            "article[itemtype*='schema.org/BlogPosting']"
        ),
        (
            "main[itemtype*='schema.org/NewsArticle'], "
            "main[itemtype*='schema.org/Article'], "
            "main[itemtype*='schema.org/BlogPosting']"
        ),
        (
            "section[itemtype*='schema.org/NewsArticle'], "
            "section[itemtype*='schema.org/Article'], "
            "section[itemtype*='schema.org/BlogPosting']"
        ),
        (
            "div[itemtype*='schema.org/NewsArticle'], "
            "div[itemtype*='schema.org/Article'], "
            "div[itemtype*='schema.org/BlogPosting']"
        ),
        (
            "article[id='article'], "
            "article[id='main'], "
            "article[role^='article'], "
            "article[role^='main']"
        ),
        "article",
        ("main[id='article'], main[id='main'], main[role^='article'], main[role^='main']"),
        "main",
        (
            "section[id='article'], "
            "section[id='main'], "
            "section[role^='article'], "
            "section[role^='main'], "
            "div[id='article'], "
            "div[id='main'], "
            "div[role^='article'], "
            "div[role^='main']"
        ),
        ("section[itemtype*='schema.org/WebPage'], div[itemtype*='schema.org/WebPage']"),
        "body",  # will default to returning body as last resort
    ]

    def __init__(
        self,
        soup: bs4.BeautifulSoup,
        metadata: dict[str, dict[str, Any]],
        config: Config,
        page_url: str = None,
    ):
        super().__init__(soup, page_url)
        self.config = config

        self.metadata = metadata
        self.inline_links_list = []

        self.top_tag = None
        self.article_text = None

    def _get_value_of_itemprop_element(
        self,
        tag: bs4.element.Tag,
    ) -> dict[str, str]:
        """Gets the name-value pairs of a tag with the `itemprop` attribute.

        The names are specified in the value of the `itemprop` attribute as
        space separated names.
        `Specification <https://html.spec.whatwg.org/multipage/microdata.html#names:-the-itemprop-attribute>`_

        The value is determined by the name of the tag, and rules are defined
        here: https://html.spec.whatwg.org/multipage/microdata.html#values4

        Written December 2020.

        Parameters
        ----------
        tag : bs4.element.Tag
            The tag with the `itemprop` attribute.

        Returns
        -------
        dict[str, str]
            A dict with key-value pairs corresponding to the name-value pairs
            added by the tag.
        """

        # https://html.spec.whatwg.org/multipage/microdata.html#names:-the-itemprop-attribute
        itemprop = tag.get("itemprop")
        assert itemprop is not None
        itemprop_list = itemprop.strip().split()
        if len(itemprop_list) == 0:
            return {}

        # https://html.spec.whatwg.org/multipage/microdata.html#values4
        if tag.name == "meta":
            value = tag.get("content")
        elif tag.name in [
            "audio",
            "embed",
            "iframe",
            "img",
            "source",
            "track",
            "video",
        ]:
            value = tag.get("src")
            if self.page_url:
                value = urljoin(self.page_url, value)
        elif tag.name in [
            "a",
            "area",
            "link",
        ]:
            value = tag.get("href")
            if self.page_url:
                value = urljoin(self.page_url, value)
        elif tag.name == "object":
            value = tag.get("data")
            if self.page_url:
                value = urljoin(self.page_url, value)
        elif tag.name == "data":
            value = tag.get("value")
        elif tag.name == "meter":
            value = tag.get("value")
        elif tag.name == "time":
            value = tag.get("datetime")
            if not value:
                value = tag.get_child_text()
        else:
            value = tag.get_text()

        return {itemprop: value for itemprop in itemprop_list}

    @staticmethod
    def _process_short_field(
        text: str,
    ) -> str:
        """Strips leading/trailing whitespace and performs NFKC normalization."""
        # strips leading and trailing whitespace
        text = text.strip()
        # normalization: replaces "\u00a0" and "\xa0" with single whitespace
        text = unicodedata.normalize("NFKC", text)
        return text

    def extract_page_url(self) -> (Optional[str], Optional[str]):
        """Extracts page URL from `self.soup`.

        Performs extraction according to the following priority:
        - Finds <link> tag in <head> with `rel="canonical"`;
          this is the most reliable method.
          (Some error handling if more than one tag found, or no tag found
          that matches the desired URL scheme)
        - Uses `url` field from OGP metadata (if non-empty)
        - Finds <link> tag in <head> with `rel="alternate"` and
          `href="x-default"`
        - Uses `url` field collected from JSON-LD metadata
          (if non-empty)

        Sets the URL found as an attribute of the class instance.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        url : str or None
            The URL of the webpage.
            `None` if the URL was not found.
        method : {"canonical", "ogp", "alternate", "json_ld", None}
            The method of extraction used.
            `None` if the URL was not found.
        """

        metadata_json_ld = self.metadata["json_ld"]
        metadata_ogp = self.metadata["opengraph"]
        best_url = None

        # find <link> tags with rel="canonical"
        canonical_list = self.soup.select("head link[rel='canonical']")
        if len(canonical_list) == 0:
            LOGGER.debug("No <link> tag with rel='canonical' found.")
        else:
            canonical_list = [
                url
                for tag in canonical_list
                if (url := tag.get("href")) is not None
                and urlparse(url).scheme in self.URL_SCHEMES
                and validate_url(url)
            ]
            if len(canonical_list) == 0:
                LOGGER.debug("No <link> tag with rel='canonical' and a matching URL found.")
            elif len(canonical_list) == 1:
                best_url = canonical_list[0]
                LOGGER.debug(
                    "Exactly one <link> tag with rel='canonical' and a matching URL found."
                )
                self.page_url = best_url
                return best_url, "canonical"
            else:
                canonical_set = set(canonical_list)
                best_url = canonical_list[0]
                self.page_url = best_url
                if len(canonical_set) > 1:
                    LOGGER.debug("More than one <link> tag with rel='canonical' found.")
                return best_url, "canonical"

        # if not None, already validated by validate_url()
        url = metadata_ogp.get("og:url")
        if validate_url(url):
            best_url = url
            self.page_url = best_url
            LOGGER.debug("Using URL from OGP metadata.")
            return best_url, "ogp"

        # find <link> tags with rel="alternate" and hreflang="x-default"
        for tag in self.soup.select("head link[rel='alternate'][hreflang]"):
            url = tag.get("href")
            if urlparse(url).scheme in self.URL_SCHEMES:
                if validate_url(url):
                    best_url = url
                    self.page_url = best_url
                    LOGGER.debug(
                        "Using <link> tag with rel='alternate' and 'hreflang' attribute present."
                    )
                    return best_url, "alternate"

        # if not None, already validated by validate_url()
        url = metadata_json_ld.get("url")
        if validate_url(url):
            best_url = url
            self.page_url = best_url
            LOGGER.debug("Using URL from JSON-LD metadata.")
            return best_url, "json_ld"

        LOGGER.info("No URL found.")
        return None, None

    def _process_author_list(
        self,
        author_list: list[dict[str, Optional[str]]],
    ) -> list[dict[str, Optional[str]]]:
        """Processes author list as extracted by `extract_authors()`.

        Removes duplicates from the list. Thereafter, attempts to combine author
        items (elements of `author_list`) that have the same `url` field.

        Only called when using CSS selectors to detect authors in HTML.

        Written January 2021.

        Parameters
        ----------
        author_list : list[dict[str, Optional[str]]]
            A non-empty list of dicts, each with the following key-value pairs:
            "name" : str or None
                The name of the author.
            "url": str or None
                The URL of the author.
            "image_url": str or None
                The image URL of the author.

        Returns
        -------
        new_author_list : list[dict[str, Optional[str]]]
            The modified author list, also nonempty, with each element having
            the same key-value pairs as above.
        """

        # remove duplicates
        author_list = [
            (item.get("name"), item.get("url"), item.get("image_url")) for item in author_list
        ]
        author_list = [
            {
                "name": item[0],
                "url": item[1],
                "image_url": item[2],
            }
            for item in set(author_list)
        ]

        # merge items with the same URL
        urls = set(item.get("url") for item in author_list if item.get("url"))

        if len(author_list) <= 1:
            return author_list
        else:
            urls = set(item.get("url") for item in author_list if item.get("url"))
            if len(urls) == len(author_list):
                return author_list

        merged_authors = {}
        merged_authors[None] = []
        for item in author_list:
            if item.get("url") is None:
                merged_authors[None].append(
                    {
                        "name": item.get("name"),
                        "image_url": item.get("image_url"),
                    }
                )
            else:
                if item.get("url") not in merged_authors:
                    merged_authors[item.get("url")] = {
                        "name": [],
                        "image_url": [],
                    }

                if item.get("name"):
                    merged_authors[item.get("url")]["name"].append(item.get("name"))
                if item.get("image_url"):
                    merged_authors[item.get("url")]["image_url"].append(item.get("image_url"))

        def get_best_author_name(author_name_list, url):
            if len(author_name_list) == 0:
                return None
            if len(author_name_list) == 1:
                return author_name_list[0]
            urlname = [y for x in url.split("/") for y in x.split("=") if y][-1]

            m = difflib.SequenceMatcher()
            m.set_seq2(urlname.lower())
            max_ratio = -1.0
            for name in author_name_list:
                m.set_seq1(name.lower())
                r = m.ratio()
                if r > max_ratio:
                    max_ratio = r
                    best_name = name
            return best_name

        def get_best_author_image_url(author_image_url_list):
            if len(author_image_url_list) == 0:
                return None
            return author_image_url_list[0]

        # create one new merged item per url
        # leave those with no url untouched
        new_author_list = []
        for url, author_items in merged_authors.items():
            if url is not None:
                author_items["name"] = list(set(author_items["name"]))
                author_items["image_url"] = list(set(author_items["image_url"]))

        for url, author_items in merged_authors.items():
            if url is not None:
                new_author_list.append(
                    {
                        "name": get_best_author_name(author_items["name"], url),
                        "url": url,
                        "image_url": get_best_author_image_url(author_items["image_url"]),
                    }
                )
            else:
                for author_item in author_items:
                    new_author_list.append(
                        {
                            "name": author_item.get("name"),
                            "url": None,
                            "image_url": author_item.get("image_url"),
                        }
                    )
        new_author_list.sort(key=lambda x: (x["name"], x["url"], x["image_url"]))
        return new_author_list

    def extract_authors(self) -> (list[dict[str, Optional[str]]], str):
        """Extracts authors from `self.soup`.

        Performs extraction according to the following priority:
        - Uses authors found from anchor tags (and thereafter other tags) in
          HTML that indicate author information, via selectors from
          `AUTHOR_SELECTORS`.
        - Uses author list from JSON-LD data (if available)
          (since this comes with the corresponding URLs for free)
        - Gets <meta> tags in <head> with `name="author"`
        - Uses author list from OGP (if available)

        Written January 2021.

        Parameters
        ----------
        None

        Returns
        -------
        author_list : list[dict[str, Optional[str]]]
            A (possibly empty) list of dicts, each with the following
            key-value pairs:
            "name": str or None
                The name of the author.
            "url": str or None
                The URL of the author.
            "image_url": str or None
                The image URL of the author.
        method : {"a", "json_ld", "head", "ogp", None}
            The method of extraction used.
            `None` if `author_list` is empty.
        """
        if self.page_url is None:
            self.extract_page_url()
        if self.base_tag is None:
            self.set_base_tag()
        if self.top_tag is None:
            self.set_top_tag()

        metadata_json_ld = self.metadata["json_ld"]
        metadata_ogp = self.metadata["opengraph"]

        author_list = []

        AUTHOR_SELECTORS = [
            (
                "a[rel='author'], "
                "a[href*='/author/'], "
                "a[href*='/author?'], "
                "a[href*='/authors/'], "
                "a[href*='/authors?']"
            ),
            (
                "a.author, "
                "a.authors, "
                "a.author-url, "
                "a.author-name, "
                "a[href*='/profile/'], "
                "a[href*='/profile?'], "
                "a[href*='/people/'], "
                "a[href*='/people?'], "
                "a[href*='/byline/'], "
                "a[href*='/byline?']"
            ),
            ("[id='penulis'], [id='author']"),
            (
                "span.author, "
                "div.author, "
                "span.author-name, "
                "div.author-name, "
                "span.articleauthor, "
                "div.articleauthor"
            ),
            ("span[class*='author'], div[class*='author']"),
            "[id='editor']",
        ]

        for container, container_name in [
            (self.top_tag, "self.top_tag"),
            (self.base_tag, "self.base_tag"),
            (self.soup.body, "self.soup.body"),
        ]:
            for selector in AUTHOR_SELECTORS:
                for tag in container.select(selector):
                    if tag.name == "a":
                        # extract URL
                        href = urljoin(self.page_url, tag.get("href"))
                        if urlparse(href).scheme not in self.URL_SCHEMES:
                            href = None
                        # get text
                        name = tag.get_text().strip()
                        if len(name) == 0:
                            name = None
                        author_item = {"name": name, "url": href}
                        # get image URL if it exists
                        img = tag.find("img")
                        if img is not None:
                            img_result = self._process_img_tag(img)
                            src = img_result.get("img_src")
                            if src is not None:
                                src = urljoin(self.page_url, src)
                                if urlparse(src).scheme not in self.URL_SCHEMES:
                                    src = None
                                author_item["image_url"] = src
                        if any(author_item.values()):
                            author_list.append(author_item)
                    else:
                        # get overall text (backup)
                        name = tag.get_text().strip()
                        if len(name) == 0:
                            name = None
                        appended = False
                        # each anchor tag corresponds to one author_item
                        for anchor_tag in tag.find_all("a"):
                            # extract URL
                            href = urljoin(self.page_url, anchor_tag.get("href"))
                            if urlparse(href).scheme not in self.URL_SCHEMES:
                                href = None
                            # get text
                            anchor_name = anchor_tag.get_text().strip()
                            if len(anchor_name) == 0:
                                anchor_name = name
                            author_item = {"name": anchor_name, "url": href}
                            # get image URL if it exists
                            img = anchor_tag.find("img")
                            if img is not None:
                                img_result = self._process_img_tag(img)
                                src = img_result.get("img_src")
                                if src is not None:
                                    src = urljoin(self.page_url, src)
                                    if urlparse(src).scheme not in self.URL_SCHEMES:
                                        src = None
                                    author_item["image_url"] = src
                            if any(author_item.values()):
                                author_list.append(author_item)
                                appended = True
                        # if there are no anchor tags in tag
                        if not appended and name:
                            author_item = {"name": name}
                            # get image URL if it exists
                            img = tag.find("img")
                            if img is not None:
                                img_result = self._process_img_tag(img)
                                src = img_result.get("img_src")
                                if src is not None:
                                    src = urljoin(self.page_url, src)
                                    if urlparse(src).scheme not in self.URL_SCHEMES:
                                        src = None
                                    author_item["image_url"] = src
                            if any(author_item.values()):
                                author_list.append(author_item)
                if len(author_list) > 0:
                    LOGGER.debug(
                        "Using authors found from container: {} using selector rule: {}".format(
                            container_name, selector
                        )
                    )
                    author_list = self._process_author_list(author_list)
                    return author_list, "a"

        json_ld_author_list = metadata_json_ld.get("author")
        if json_ld_author_list is not None:
            if len(json_ld_author_list) != 0:
                author_list = json_ld_author_list
                LOGGER.debug("Using author list from JSON-LD metadata.")
                return self._process_author_list(author_list), "json_ld"

        for tag in self.soup.select("head meta[name='author']"):
            x = tag.get("content")
            if x:
                if x.startswith(("http://", "https://", "ftp://", "//")):
                    author_list.append({"name": None, "url": x})
                else:
                    author_list.append({"name": x, "url": None})
        if len(author_list) > 0:
            LOGGER.debug("Using authors from <meta> tags in <head>.")
            return self._process_author_list(author_list), "head"

        ogp_author_list = metadata_ogp.get("article:author")
        if len(ogp_author_list) != 0:
            for x in ogp_author_list:
                # check if author is a URL instead of a proper name
                if x.startswith(("http://", "https://", "ftp://", "//")):
                    author_list.append({"name": None, "url": x})
                else:
                    author_list.append({"name": x, "url": None})
            LOGGER.debug("Using author list from OGP metadata.")
            return self._process_author_list(author_list), "ogp"

        LOGGER.info("No authors found.")
        return [], None

    def extract_description(self) -> (Optional[str], Optional[str]):
        """Extracts article description from `self.soup`.

        Performs extraction according to the following priority:
        - Gets <meta> tag(s) in <head> with `name="description"`
        - Uses description from JSON-LD metadata (if available)
        - Uses description from OGP metadata (if available)
        - Gets <meta> tag(s) in <head> with `name="twitter:description"`

        Written February 2021.

        Parameters
        ----------
        None

        Returns
        -------
        description : str or None
            The description of the article.
        method : {"head", "json_ld", "ogp", "twitter", None}
            The method of extraction used.
            `None` if no description was found.
        """
        if self.page_url is None:
            self.extract_page_url()

        metadata_json_ld = self.metadata["json_ld"]
        metadata_ogp = self.metadata["opengraph"]

        description = None

        # assumes that only one such tag can exist
        description_tag = self.soup.select_one("head meta[name='description']")
        if description_tag is not None:
            description = description_tag.get("content")
            if description is not None:
                LOGGER.debug("Using description from <head>.")
                return self._process_short_field(description), "head"

        description = metadata_json_ld.get("description")
        if description is not None:
            LOGGER.debug("Using description from JSON-LD metadata.")
            return self._process_short_field(description), "json_ld"

        description = metadata_ogp.get("og:description")
        if description is not None:
            LOGGER.debug("Using description from OGP metadata.")
            return self._process_short_field(description), "ogp"

        # assumes that only one such tag can exist
        description_tag = self.soup.select_one("head meta[name='twitter:description']")
        if description_tag is not None:
            description = description_tag.get("content")
            if description is not None:
                LOGGER.debug("Using description from 'twitter:description' <meta> tag.")
                return self._process_short_field(description), "twitter"

        LOGGER.info("No description found.")
        return None, None

    def extract_language(self) -> (Optional[str], Optional[str]):
        """Gets BCP47 language tag of HTML document.

        The language tag is a string that conforms to the
        `specification <https://www.ietf.org/rfc/bcp/bcp47.txt>`_
        It is case insensitive (section 2.1.1), but convention (section 2.1.1)
        suggests that:
        - language codes be written in lowercase;
        - script codes be written in Sentence case;
        - country codes be written in CAPITAL CASE.
        (e.g. `mn-Cyrl-MN` for Mongolian in the Cyrillic script in Mongolia)

        Performs extraction according to the following priority:
        - Uses `lang` attribute of <html>
        - Uses `inLanguage` field of JSON-LD metadata (if available)
        - Uses `og:locale` field of OGP metadata (if available)

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        lang : str or None
            The language tag of the article, according to BCP47.
        method : {"html", "json_ld", "ogp", None}
            The method of extraction used.
            `None` if no language tag found.
        """
        if self.page_url is None:
            self.extract_page_url()

        metadata_json_ld = self.metadata["json_ld"]
        metadata_ogp = self.metadata["opengraph"]

        lang = self.soup.html.get("lang")
        if language_tags.tags.check(lang):
            LOGGER.debug("Using language tag from <html>.")
            return language_tags.tags.tag(lang).format, "html"

        lang = metadata_json_ld.get("inLanguage")
        if language_tags.tags.check(lang):
            LOGGER.debug("Using language tag from JSON-LD metadata.")
            return language_tags.tags.tag(lang).format, "json_ld"

        lang = metadata_ogp.get("og:locale")
        if lang:
            lang = lang.replace("_", "-")
            if not re.fullmatch(r"[a-zA-Z0-9-]+", lang):
                LOGGER.debug("OGP language tag contains special characters: {}".format(lang))
        if language_tags.tags.check(lang):
            LOGGER.debug("Using language tag from OGP metadata.")
            return language_tags.tags.tag(lang).format, "ogp"

        LOGGER.info("No language tag found.")
        return None, None

    def extract_keywords(self) -> (list[str], list[str]):
        """Extracts article keywords from `self.soup`.

        Performs extraction according to the following priority:
        - Uses `keywords` field collected from JSON-LD metadata
          (if non-empty)
        - Uses `article:tag` field from OGP metadata (if non-empty)
        - Gets <meta> tags in <head> with `name='keywords'`, if non-empty
          (this is a comma-separated list of tags)
        - Gets <meta> tags in <head> with `name='news_keywords'`, if non-empty
          (this is a comma-separated list of tags)
        - Gets <a> tags with `rel="tag"`
        - Gets <a> tags with `href` a URL that represents a tag

        Written February 2021.

        Parameters
        ----------
            None

        Returns
        -------
        all_keywords : list[str]
            A list (possibly empty) of keywords of the article.
        method : list[str]
            The methods of extraction used, from the following:
            "json_ld", "ogp", "keywords", "news_keywords", "anchor"
        """
        if self.page_url is None:
            self.extract_page_url()

        A_REL_TAG_SELECTOR = "a[rel='tag']"
        A_HREF_TAG_SELECTOR = "a[href*='/tag/'], a[href*='/tags/']"

        metadata_json_ld = self.metadata["json_ld"]
        metadata_ogp = self.metadata["opengraph"]

        all_keywords = set()
        methods = []

        keywords = set(metadata_json_ld.get("keywords"))
        if len(keywords) > 0:
            if not keywords.issubset(all_keywords):
                LOGGER.debug("Using keywords from JSON-LD metadata.")
                all_keywords.update(keywords)
                methods.append("json_ld")

        keywords = set(metadata_ogp.get("article:tag"))
        if not keywords.issubset(all_keywords):
            LOGGER.debug("Using keywords from OGP metadata.")
            all_keywords.update(keywords)
            methods.append("ogp")

        # assumes that not more than one such tag will exist:
        # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta/name
        meta_tag = self.soup.select_one("head meta[name='keywords']")
        if meta_tag is not None:
            tagstring = meta_tag.get("content")
            keywords = set(x.strip() for x in tagstring.split(",") if x and len(x.strip()) > 0)
            if not keywords.issubset(all_keywords):
                LOGGER.debug("Using keywords from <meta> tag with name='keywords'.")
                all_keywords.update(keywords)
                methods.append("keywords")

        # assumes that not more than one such tag will exist
        meta_tag = self.soup.select_one("head meta[name='news_keywords']")
        if meta_tag is not None:
            tagstring = meta_tag.get("content")
            keywords = set(x.strip() for x in tagstring.split(",") if x and len(x.strip()) > 0)
            if not keywords.issubset(all_keywords):
                LOGGER.debug("Using keywords from <meta> tag with name='news_keywords'.")
                all_keywords.update(keywords)
                methods.append("news_keywords")

        keywords = set()
        for selector in [A_REL_TAG_SELECTOR, A_HREF_TAG_SELECTOR]:
            for a_tag in self.soup.select(selector):
                tagstr = a_tag.string
                if tagstr:
                    tagstr = str(tagstr).strip()
                    keywords.add(tagstr)
        if not keywords.issubset(all_keywords):
            LOGGER.debug("Using keywords via anchor tags in HTML.")
            all_keywords.update(keywords)
            methods.append("anchor")

        if len(all_keywords) == 0:
            LOGGER.info("No keywords found.")
            return [], []
        else:
            all_keywords = self._process_keywords_list(list(all_keywords))
            return list(all_keywords), methods

    def _process_keywords_list(
        self,
        keywords: list[str],
    ) -> list[str]:
        """Processes keywords list found by `extract_keywords()`.

        Performs the following:
        - String normalization of each keyword (using `_process_short_field()`);
        - Removes duplicates (case-sensitive);
        - For case-insensitive removal of duplicates, selects one
          "representative" to preserve, according to the following priority:
            Title Case, UPPERCASE, lowercase, oTherCasE
        - Sorts the list of keywords.

        Written February 2021.

        Parameters
        ----------
        keywords : list[str]
            The original list of keywords.

        Returns
        -------
        new_keywords : list[str]
            The modified list of keywords.
        """

        # short text preprocessing
        keywords = [self._process_short_field(x) for x in keywords]

        # remove duplicates
        keywords = list(set(keywords))

        collector = defaultdict(list)
        for keyword in keywords:
            collector[keyword.lower()].append(keyword)
        new_keywords = []
        for key, option_list in collector.items():
            if len(option_list) == 0:
                continue
            if len(option_list) == 1:
                new_keywords.append(option_list[0])
                continue
            title = None
            upper = None
            lower = None
            for option in option_list:
                if option.istitle():
                    title = option
                elif option.isupper():
                    upper = option
                elif option.islower():
                    lower = option
            if title:
                new_keywords.append(title)
            elif upper:
                new_keywords.append(upper)
            elif lower:
                new_keywords.append(lower)
            else:
                new_keywords.append(option_list[0])
        return sorted(new_keywords)

    def extract_timestamps(
        self,
    ) -> (dict[str, Optional[str]], dict[str, Optional[str]]):
        """Extracts timestamps from `self.soup`.

        Identifies if the webpage records two different timestamps:
        - the time at which the webpage was published;
        - the time at which the webpage was modified.

        For the former, performs extraction according to the following priority:
        - Uses `datePublished` field collected from JSON-LD metadata
          (if non-empty)
        - Uses `article:published_time` field collected from OGP metadata
          (if non-empty)
        - Uses `dateCreated` field collected from JSON-LD metadata
          (if non-empty)
        - Finds a <time> tag with `itemprop` containing `"datePublished"`,
          then accesses its `datetime` attribute
        - Finds a <meta> tag with `itemprop` containing `"datePublished"`,
          then accesses its `content` attribute

        For the latter, performs extraction according to the following priority:
        - Uses `dateModified` field collected from JSON-LD metadata
          (if non-empty)
        - Uses `article:modified_time` field collected from OGP metadata
          (if non-empty)
        - Finds a <time> tag with `itemprop` containing `"dateModified"`,
          then accesses its `datetime` attribute
        - Finds a <meta> tag with `itemprop` containing `"dateModified"`,
          then accesses its `content` attribute

        JSON-LD times take precedence because they are more likely to capture
        timezone info correctly.

        Both times are formatted according to `parse_dt_str()`.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        timestamps: dict[str, Optional[str]]
            A dict with the following key-value pairs:
            "record_published_isotimestamp" : str or None
                The time of publication.
            "record_modified_isotimestamp" : str or None
                The time last modified.
        methods: dict[str, Optional[str]]
            A dict with the following key-value pairs:
            "record_published_isotimestamp" : str or None
                The method of extraction used.
            "record_modified_isotimestamp" : str or None
                The method of extraction used.
            The values can be one of the following:
            "json_ld", "ogp", "time", "meta"
        """
        if self.page_url is None:
            self.extract_page_url()

        metadata_json_ld = self.metadata["json_ld"]
        metadata_ogp = self.metadata["opengraph"]
        published_method = None
        modified_method = None

        # datePublished from JSON-LD data
        published_isotimestamp = metadata_json_ld.get("datePublished")
        if published_isotimestamp is not None:
            published_method = "json_ld"

        # published_time from OGP
        if published_isotimestamp is None:
            published_isotimestamp = metadata_ogp.get("article:published_time")
        if published_isotimestamp is not None:
            published_method = "ogp"

        # dateCreated from JSON-LD data
        if published_isotimestamp is None:
            published_isotimestamp = metadata_json_ld.get("dateCreated")
        if published_isotimestamp is not None:
            published_method = "json_ld"

        # datetime value from <time> elements with itemprop,
        # containing the name 'datePublished'
        if published_isotimestamp is None:
            for tag in self.soup.select("time[itemprop~='datePublished']"):
                published_isotimestamp = parse_dt_str(tag.get("datetime"))
                if published_isotimestamp is not None:
                    break
        if published_isotimestamp is not None:
            published_method = "time"

        # content value from <meta> elements with itemprop,
        # containing the name 'datePublished'
        if published_isotimestamp is None:
            for tag in self.soup.select("meta[itemprop~='datePublished']"):
                published_isotimestamp = parse_dt_str(tag.get("content"))
                if published_isotimestamp is not None:
                    break
        if published_isotimestamp is not None:
            published_method = "meta"

        # dateModified from JSON-LD data
        modified_isotimestamp = metadata_json_ld.get("dateModified")
        if modified_isotimestamp is not None:
            modified_method = "json_ld"

        # modified_time from OGP
        if modified_isotimestamp is None:
            modified_isotimestamp = metadata_ogp.get("article:modified_time")
        if modified_isotimestamp is not None:
            modified_method = "ogp"

        # datetime value from <time> elements with itemprop,
        # containing the name 'dateModified'
        if modified_isotimestamp is None:
            for tag in self.soup.select("time[itemprop~='dateModified']"):
                modified_isotimestamp = parse_dt_str(tag.get("datetime"))
                if modified_isotimestamp is not None:
                    break
        if modified_isotimestamp is not None:
            modified_method = "time"

        # content value from <meta> elements with itemprop,
        # containing the name 'dateModified'
        if modified_isotimestamp is None:
            for tag in self.soup.select("meta[itemprop~='dateModified']"):
                modified_isotimestamp = parse_dt_str(tag.get("content"))
                if modified_isotimestamp is not None:
                    break
        if modified_isotimestamp is not None:
            modified_method = "meta"

        if published_method is None:
            LOGGER.info("No published_isotimestamp found.")
        else:
            LOGGER.debug("Using published_isotimestamp via method: {}".format(published_method))
        if modified_method is None:
            LOGGER.info("No modified_isotimestamp found.")
        else:
            LOGGER.debug("Using modified_isotimestamp via method: {}".format(modified_method))
        return (
            {
                "record_published_isotimestamp": published_isotimestamp,
                "record_modified_isotimestamp": modified_isotimestamp,
            },
            {
                "record_published_isotimestamp": published_method,
                "record_modified_isotimestamp": modified_method,
            },
        )

    def extract_title(
        self,
        clean: bool = True,
    ) -> (str, str):
        """Extracts article title from `self.soup`.

        Performs extraction according to the following priority:
        - Uses `headline` field collected from JSON-LD metadata (if non-empty)
        - Uses `name` field collected from JSON-LD metadata (if non-empty)
        - Uses `title` field from OGP metadata (if non-empty)
        - Finds elements with `itemprop` attribute containing `"headline"`
        - Gets <h1> tag (if there is only one such tag) and use its text
        - Gets <h1> tag with `class` or `id` attributes containing
          `"title"` or `"headline"`
        - Gets text of <title> tag, either:
            - in <head>, or
            - failing that (malformed HTML), in <html>
          then perform optional cleaning
          (such as to remove "multi-part" titles).

        Written February 2021.

        Parameters
        ----------
        clean : bool
            Whether to perform cleaning of text in <title> tag.

        Returns
        -------
        title : str or None
            The title for the article.
        method : {"json_ld_headline", "json_ld_name", "ogp",
                  "itemprop_headline", "h1", "h1_title_headline",
                  "title", "title_cleaned", None}
            The method of extraction used.
            `None` if no title found.
        """
        if self.page_url is None:
            self.extract_page_url()

        metadata_json_ld = self.metadata["json_ld"]
        metadata_ogp = self.metadata["opengraph"]

        title = metadata_json_ld.get("headline")
        if title is not None:
            LOGGER.debug("Using title from 'headline' field in JSON-LD metadata.")
            return self._process_short_field(title), "json_ld_headline"
        title = metadata_json_ld.get("name")
        if title is not None:
            LOGGER.debug("Using title from 'name' field in JSON-LD metadata.")
            return self._process_short_field(title), "json_ld_name"
        title = metadata_ogp.get("og:title")
        if title is not None:
            LOGGER.debug("Using title from OGP metadata.")
            return self._process_short_field(title), "ogp"

        def tag_has_itemprop_headline(tag):
            itemprop = tag.get("itemprop")
            if not itemprop:
                return False
            return "headline" in itemprop.strip().split()

        itemprop_list = self.soup.find_all(tag_has_itemprop_headline)
        for title_tag in itemprop_list:
            title = self._get_value_of_itemprop_element(title_tag).get("headline")
            if title:
                LOGGER.debug("Using title from tags with itemprop containing 'headline'.")
                return self._process_short_field(title), "itemprop_headline"

        h1_list = self.soup.find_all("h1")
        if len(h1_list) == 1:
            title = h1_list[0].get_text().strip()
            if len(title) > 0:
                LOGGER.debug("Using title from the only <h1> tag.")
                return self._process_short_field(title), "h1"
        elif len(h1_list) > 1:
            h1_id_list = self.soup.select("h1[id*='title']")
            if h1_id_list:
                LOGGER.debug("Using title from <h1> tag with id='title'.")
                return self._process_short_field(h1_id_list[0].get_text()), "h1_title_headline"
            h1_id_list = self.soup.select("h1[id*='headline']")
            if h1_id_list:
                LOGGER.debug("Using title from <h1> tag with id='headline'.")
                return self._process_short_field(h1_id_list[0].get_text()), "h1_title_headline"
            h1_class_list = self.soup.select("h1[class*='title']")
            if h1_class_list:
                LOGGER.debug("Using title from <h1> tag with class containing 'title'.")
                return (
                    self._process_short_field(h1_class_list[0].get_text()),
                    "h1_title_headline",
                )
            h1_class_list = self.soup.select("h1[class*='headline']")
            if h1_class_list:
                LOGGER.debug("Using title from <h1> tag with class containing 'headline'.")
                return (
                    self._process_short_field(h1_class_list[0].get_text()),
                    "h1_title_headline",
                )

        # Extract title from the html > head > title tag.
        # The HTML document MUST contain exactly one <head> element followed by
        # exactly one <body> element. The <head> element MUST contain exactly
        # one <title> tag, which must contain 'Text that is not inter-element
        # whitespace':
        # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/title
        head_tag = self.soup.head
        if head_tag is None:
            LOGGER.debug("No <head> tag found in <html>!")
            title_tag = self.soup.title
        else:
            title_tag = head_tag.title
            if title_tag is None:
                LOGGER.debug("No <title> tag found in <head>!")
                title_tag = self.soup.title
        if title_tag is None:
            LOGGER.debug("No <title> tag found in <html>!")
            return None, None

        title = title_tag.string.strip()
        if not clean:
            LOGGER.debug("Using title from <title> tag!")
            return self._process_short_field(title), "title"

        TITLE_REGEX = re.compile(
            r"""
                \s+  # 1 or more whitespace chars
                [-–|]  # separator: - or – or |
                \s+  # 1 or more whitespace chars
            """,
            re.X,
        )

        matchlist = re.split(TITLE_REGEX, title)
        matchlist = [x.strip() for x in matchlist if len(x.strip()) > 0]
        if len(matchlist) == 0:
            LOGGER.debug("No parts found in <title>!")
            LOGGER.info("No title found.")
            return None, None
        else:
            title = max(matchlist, key=len)
            LOGGER.debug("Using title from <title> tag!")
            return self._process_short_field(title), "title_cleaned"

    def set_base_tag(self) -> None:
        """Sets the base tag from which to extract assets.

        The base node is a tag that most likely contains all content of a news
        article, including the title, headline, banner images, author(s), date
        information, paragraph text, embedded media, and tags.

        Uses a list of CSS selectors in `self.BASE_TAG_SELECTORS` to
        select tags from `self.soup`.
        For each selection of tags, choose the largest tag (with the most
        characters) and uses it as the base tag if it contains at least
        `self.config.BASE_TAG_CHARS_RATIO` characters of the total.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If no selector in `self.BASE_TAG_SELECTORS` is successful.

        See Also
        --------
        AssetExtractor.set_base_tag : method overwritten.
        """
        tc = int(self.soup.body.get("_ld_tc"))
        count = 0
        for selector in self.BASE_TAG_SELECTORS:
            choices = list(self.soup.select(selector))
            count += 1
            if len(choices) == 0:
                continue
            else:
                largest_choice = max(choices, key=lambda x: int(x.get("_ld_tc")))
            largest_choice_tc = int(largest_choice.get("_ld_tc"))
            if largest_choice_tc / tc > self.config.BASE_TAG_CHARS_RATIO:
                LOGGER.debug(
                    "Stage {}: ".format(count)
                    + "Found base tag <{}> - ".format(largest_choice.name)
                    + "{} of {} characters.".format(largest_choice_tc, tc)
                )
                self.base_tag = largest_choice
                return
        else:
            # In practice, never raised because the last selector in
            # `BASE_TAG_SELECTORS` is the body itself.
            raise ValueError

    @staticmethod
    def _get_lowest_common_ancestor(
        tag_list: list[bs4.element.Tag],
    ) -> bs4.element.Tag:
        """Returns the lowest common ancestor of tags in `tag_list`.

        A lowest common ancestor is a `bs4.element.Tag` object that contains
        every tag in `tag_list` as a descendant, and is such that no descendant
        of it has the same property.

        (We consider a tag to be a descendant of itself.)

        Since <html> is always a possible common ancestor, and never appears in
        `tag_list`, the lowest always exists.

        Written December 2020.

        Parameters
        ----------
        tag_list : list[bs4.element.Tag]
            The list of `bs4.element.Tag` objects to find the ancestor of.

        Returns
        -------
        bs4.element.Tag
            The lowest common ancestor.
        """
        if len(tag_list) == 0:
            return None
        elif len(tag_list) == 1:
            return tag_list[0]
        tag, my_tag_list = tag_list[-1], tag_list[:-1]  # remove and return last tag
        for parent in tag.find_parents(True):
            my_tag_list = [
                other_tag for other_tag in my_tag_list if parent not in other_tag.parents
            ]
            if len(my_tag_list) == 0:
                return parent

    @staticmethod
    def _get_ancestral_distance(
        ancestor: bs4.element.Tag,
        tag: bs4.element.Tag,
    ) -> int:
        """Returns the ancestral distance between `ancestor` and `tag`.

        `tag` is guaranteed to be either equal to `ancestor`, or its descendant.

        The ancestral distance is the number of edges in the shortest path from
        `ancestor` and `tag`, treating the HTML document as a tree, and two
        `bs4.element.PageElement` objects being connected if one is a parent of
        another.

        Written December 2020.

        Parameters
        ----------
        ancestor : bs4.element.Tag
            The ancestor tag.
        tag : bs4.element.Tag
            The descendant tag.

        Returns
        -------
        int
            The number of levels, a non-negative integer.

        Raises
        ------
        ValueError
            If `tag` is not equal to `ancestor`,
            or if `tag` is not a descendant of `ancestor`.
        """
        if not (tag is ancestor) and not (tag in list(ancestor.find_all(True))):
            LOGGER.error(
                "tag is not equal to ancestor or its descendant!"
                + "ancestor: {}, tag: {},".format(ancestor, tag)
            )
            raise ValueError
        i = 0
        if tag is ancestor:
            return i
        for parent in tag.parents:
            i += 1
            if parent is ancestor:
                return i
        else:
            raise ValueError

    def _get_best_common_ancestor(
        self,
        tag_list: list[bs4.element.Tag],
    ) -> bs4.element.Tag:
        """Finds the best common ancestor of a list of `bs4.element.Tag` tags.

        Given a list of `bs4.element.Tag` objects, find an ancestor
        `bs4.element.Tag` that contains the largest subset of them as
        descendants, such the maximum distance between the ancestor and any
        tag is not greater than `self.config.MAX_LEVELS`.

        (We consider a tag to be a descendant of itself.)

        The size of a subset of tags is the number of total characters in all
        the tags.

        Break ties by minimizing the maximum distance between the ancestor and
        any tag in the subset.

        Starting from `ancestor` as returned from
        `get_lowest_common_ancestor()`, repeatedly replace it with the child tag
        with the largest subset of tags from `tag_list`, until the maximum
        distance to the subset is not greater than `self.config.MAX_LEVELS`.
        Also keep track of the subset of tags in `current_tag_list`.

        Thereafter, `ancestor` may have a child tag which contains the same
        subset; resolve that by returning the lowest common ancestor of
        `current_tag_list`.

        Written December 2020.

        Parameters
        ----------
        tag_list : list[bs4.element.Tag]
            The list of `bs4.element.Tag` objects to find the ancestor of.

        Returns
        -------
        bs4.element.Tag
            The best common ancestor.
        """
        if len(tag_list) == 0:
            return None
        elif len(tag_list) == 1:
            return tag_list[0]

        # get lowest common ancestor;
        # this is guaranteed to contain all tags in tags_list as descendants.
        grandparent = self._get_lowest_common_ancestor(tag_list)
        LOGGER.debug("Found lowest common ancestor of tag list.")

        # perform top-down search over candidates
        current = grandparent
        current_tag_list = tag_list
        while True:
            # current contains the largest subset of tags so far
            # however, distance from current to children could be large
            distances = [self._get_ancestral_distance(current, tag) for tag in current_tag_list]
            near = all(d <= self.config.MAX_LEVELS for d in distances)
            if near:
                # current is sufficiently near; either return it or its children
                break

            # current is too far away; must assign a direct child tag to current
            candidates = list(current.find_all(recursive=False))

            # find the "best candidate" among direct child tags
            best_candidate = None
            best_candidate_sum = 0
            for candidate in candidates:
                candidate_tag_list = [
                    tag
                    for tag in current_tag_list
                    if bool((candidate is tag) or (candidate in tag.parents))
                ]
                candidate_sum = sum(int(tag.get("_ld_tc")) for tag in candidate_tag_list)
                if candidate_sum > best_candidate_sum:
                    best_candidate = candidate
                    best_candidate_sum = candidate_sum
                    best_candidate_tag_list = candidate_tag_list

            current = best_candidate
            current_tag_list = best_candidate_tag_list

        LOGGER.debug("Current ancestor candidate is now near enough to taglist!")

        # at this point, current is a common ancestor of
        # all tags in current_tag_list; we seek lowest common ancestor
        return self._get_lowest_common_ancestor(current_tag_list)

    def set_top_tag(self) -> None:
        """Sets the top tag, containing article text, in `self.top_tag`.

        Converges to a `bs4.element.Tag` object that "best" represents the
        article text of the document.

        Starting from a loose bound (a tag that is most likely an ancestor of
        the desired output):
        1) Finds all <p> tags in this loose bound;
           (If there are no <p> tags (due to poorly formatted HTML),
           fallback to other tags that are likely to format paragraphs)
        2) Finds the most common CSS selector expression to these tags;
        3) Finds the "best ancestor" to the subset of tags from (2),
           as returned by `self._get_best_common_ancestor()`.

        This indirect strategy is used because:
        - We can't rely on all documents to have <p> tags;
        - We can't rely on all <p> tags to have the same parent, or the
          same parent's parent;
        - We can't rely on all paragraphs to be at the same level in the DOM;

        When found, sets this node as `self.top_tag`. This is guaranteed to
        be a descendant of (possibly equal to) `self.base_tag`.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        # loose bound on the largest possible tag to return
        if not self.base_tag:
            self.set_base_tag()

        # first run through to find a suitable set with link_density
        for choices in self.TAGS_TO_CHECK_LISTS:
            tags_to_check = list(self.base_tag.find_all(choices))
            if len(tags_to_check) == 0:
                LOGGER.info("No tags from {} detected in base node.".format(choices))
                continue

            # filters out tags with high link density;
            # these tags are likely navigation headings etc.
            tags_to_check_low_ld = [
                tag
                for tag in tags_to_check
                if float(tag.get("_linkdensity")) < self.config.LINKDENSITY_UPPERBOUND
            ]
            if len(tags_to_check_low_ld) >= self.config.MIN_TAGS_TO_CHECK:
                tags_to_check = tags_to_check_low_ld

            # Find the largest subset of choice tags that have the same CSS
            # selector (up to the parent)
            css_dict = defaultdict(list)
            css_counter = Counter()

            for tag in tags_to_check:
                skip_check = True
                for child in tag.contents:
                    # skips check for all elements that:
                    # 1) do not contain text as direct children, and
                    # 2) all direct children tags are already in tags_to_check
                    if isinstance(child, bs4.element.NavigableString):
                        if re.fullmatch(r"\s*", child) is None:
                            # tag contains text as direct child
                            skip_check = False
                            break
                    elif isinstance(child, bs4.element.Tag):
                        if child not in tags_to_check:
                            skip_check = False
                            break
                if skip_check:
                    continue
                # include all paths that "look the same":
                # required since sometimes <p> tags do not share a parent
                parent_css = get_css_selector_of_soup_tag(tag.parent, reduced=True)
                css_dict[parent_css].append(tag)
                css_counter[parent_css] += int(tag.get("_ld_tc"))

            # number of characters in all the tags
            parent_css = css_counter.most_common(1)[0][0]
            tag_list = css_dict[parent_css]  # guaranteed non-empty
            # at this stage, the tags in tag_list NEED NOT have a common parent.

            self.top_tag = self._get_best_common_ancestor(tag_list)
            return
        else:
            LOGGER.info("Setting top_tag to base_tag.")
            self.top_tag = self.base_tag
            return

    def remove_high_linkdensity_sections(self, tag: bs4.element.Tag) -> bs4.element.Tag:
        """Removes sections of high link-density from `self.top_tag`.

        Sections that may be removed are defined in `SECTIONING_TAGS`.
        Decomposes all such sections which have a link-density greater
        than `self.config.LINKDENSITY_UPPERBOUND`.

        Written December 2020.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # assert top_tag.parent is None
        SECTIONING_TAGS = [
            # Content sectioning
            # "article",
            # "aside", "footer", "header", "nav",
            "section",
            # Text content
            "div",
            "ol",
            "ul",
        ]
        while True:
            for sectioning_tag in tag.find_all(SECTIONING_TAGS):
                link_density = sectioning_tag.get("_linkdensity")
                if float(link_density) > self.config.LINKDENSITY_UPPERBOUND:
                    sectioning_tag.decompose()
                    break
            else:  # reached if no tag was decomposed
                return tag

    def _process_paragraph_tag(
        self,
        tag: bs4.element.Tag,
    ) -> None:
        """Removes anchor tags from paragraphs, and formats text.

        Given a `bs4.element.Tag` object representing a paragraph:
        - unwraps anchor tags, keeping the child text, with appropriate
          whitespace formatting
        - adds the anchor tag text and URL to `self.inline_links_list`
          for further processing

        `tag` is modified in-place.

        Written December 2020.

        Parameters
        ----------
        tag : bs4.element.Tag
            The paragraph tag.

        Returns
        -------
        None
        """

        tag.smooth()  # joins two or more adjacent NavigableString objects
        for markup_tag in tag.find_all(self.config.MARKUP_TAGS + ["a"]):
            if markup_tag.name == "a":
                # Processing anchor tag
                anchor_text = markup_tag.get_text()
                anchor_href = markup_tag.get("href")
                self.inline_links_list.append(
                    {
                        "text": anchor_text,
                        "url": anchor_href,
                    }
                )

            # Text formatting
            current = markup_tag
            while True:
                left = current.previous_sibling
                if left:
                    break
                else:
                    current = current.parent
                    if current is tag:
                        break
            if left:
                # gets rightmost string left of markup_tag
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
            current = markup_tag
            while True:
                right = current.next_sibling
                if right:
                    break
                else:
                    current = current.parent
                    if current is tag:
                        break
            if right:
                # gets leftmost string right of markup_tag
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
            markup_tag.unwrap()
        tag.smooth()  # joins two or more adjacent NavigableString objects
        return

    def get_article_text(
        self,
    ) -> str:
        """Produces article text from a HTML document.

        Given `self.top_tag`, retrieves tags that are likely to represent
        body text (defined in `self.TEXT_TAGS`). If too little text is found,
        include other tags as defined in `self.BACKUP_TEXT_TAGS`.

        For each tag, process it with `_process_paragraph_tag()`, which includes
        extracting any hyperlinks and storing it in `self.inline_links_list`,
        and obtain its text.

        Written February 2021.

        Parameters
        ----------
        None

        Returns
        -------
        article_text : list[str]
            A list, with each element representing text from a paragraph.
        """
        # calculate top_tag if not yet done
        if not self.top_tag:
            self.set_top_tag()

        top_tag = copy.copy(self.top_tag)
        top_tag = self.remove_high_linkdensity_sections(top_tag)

        for choices in self.TEXT_TO_COLLECT_LISTS:
            current_sum = sum(int(x.get("_ld_tc")) for x in top_tag.find_all(choices))
            LOGGER.debug("{} characters found, from tags in: {}".format(current_sum, choices))
            try:
                ratio = current_sum / int(top_tag.get("_ld_tc"))
            except ZeroDivisionError:
                ratio = 0.0
            if ratio >= self.config.ARTICLE_TEXT_CHARS_RATIO:
                break
        else:
            # error reporting
            choices = self.TEXT_TO_COLLECT_LISTS[-1]

        text_list = []
        if top_tag.name in choices:
            tags_list = [top_tag] + top_tag.find_all(choices)
        else:
            tags_list = top_tag.find_all(choices)
        # tags_list may contain duplicated content from nested tags.

        while tags_list:
            tag = tags_list.pop(0)

            # check if tag contains text
            skip_check = True
            # TEXT_TO_COLLECT_LISTS[0] contains flow tags,
            # we don't want to skip them
            if tag.name in self.TEXT_TO_COLLECT_LISTS[0]:
                skip_check = False
            for child in tag.contents:
                if isinstance(child, bs4.element.NavigableString):
                    if re.fullmatch(r"\s*", child) is None:
                        # tag contains text as direct child
                        skip_check = False
                elif isinstance(child, bs4.element.Tag):
                    # if every single child is already in tags_list,
                    # don't check the parent
                    if child not in tags_list:
                        skip_check = False
            if skip_check:
                continue

            # remove any descendant duplicated in tags_list
            for child in tag.find_all(choices):
                if child in tags_list:
                    tags_list.remove(child)

            # process the tag
            self._process_paragraph_tag(tag)
            text = tag.get_text()
            # Verified: splitting text to remove extra whitespace is necessary?
            text = " ".join(text.strip().split())
            if len(text) > 0:
                text_list.append(text)

        self.inline_links_list = self._process_link_list(self.inline_links_list)

        self.article_text = text_list
        return self.article_text
