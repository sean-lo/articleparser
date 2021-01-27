"""Definitions of named constants for the package.

Written January 2021.
"""

# Python 3.7 onwards, for annotations with standard collections
from __future__ import annotations

EMPTY_TAGS = [  # https://developer.mozilla.org/en-US/docs/Glossary/empty_elements
    # Document metadata
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "keygen",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
]

METADATA_TAGS = [  # https://html.spec.whatwg.org/multipage/dom.html#metadata-content-2
    # https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Content_categories#Metadata_content
    "base",
    "link",
    "meta",
    "noscript",
    "script",
    "style",
    "template",
    "title",
    # obsolete
    "command",
]

FLOW_TAGS = [  # https://html.spec.whatwg.org/multipage/dom.html#flow-content-2
    # https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Content_categories#Flow_content
    "a",
    "abbr",
    "address",
    "area",  # if descendant of <map> element
    "article",
    "aside",
    "audio",
    "b",
    "bdi",
    "bdo",
    "blockquote",
    "br",
    "button",
    "canvas",
    "cite",
    "code",
    "data",
    "datalist",
    "del",
    "details",
    "dfn",
    "dialog",
    "div",
    "dl",
    "em",
    "embed",
    "fieldset",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hgroup",
    "hr",
    "i",
    "iframe",
    "img",
    "input",
    "ins",
    "kbd",
    "label",
    "link",  # if allowed in <body> # if 'itemprop' attribute is present
    "main",  # if it is a hierarchially corrent <main> element
    "map",
    "mark",
    "math",
    "menu",
    "meta",  # if 'itemprop' attribute is present
    "meter",
    "nav",
    "noscript",
    "object",
    "ol",
    "output",
    "p",
    "picture",
    "pre",
    "progress",
    "q",
    "ruby",
    "s",
    "samp",
    "script",
    "section",
    "select",
    "slot",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "svg",
    "table",
    "template",
    "textarea",
    "time",
    "u",
    "ul",
    "var",
    "video",
    "wbr",
    # obsolete
    "command",
    # deprecated
    "keygen",
]

SECTIONING_TAGS = [  # https://html.spec.whatwg.org/multipage/dom.html#sectioning-content-2
    # https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Content_categories#Sectioning_content
    "article",
    "aside",
    "nav",
    "section",
]

# https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Content_categories#Heading_content
HEADING_TAGS = [
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hgroup",
]

PHRASING_TAGS = [  # https://html.spec.whatwg.org/multipage/dom.html#phrasing-content-2
    # https://developer.mozilla.org/en-US/docs/Web/Guide/HTML/Content_categories#Phrasing_content
    "a",  # if it contains only phrasing content
    "abbr",
    "area",  # if it is a descendant of <map>
    "audio",
    "b",
    "bdi",
    "bdo",
    "br",
    "button",
    "canvas",
    "cite",
    "code",
    "data",
    "datalist",
    "del",  # if it contains only phrasing content
    "dfn",
    "em",
    "embed",
    "i",
    "iframe",
    "img",
    "input",
    "ins",  # if it contains only phrasing content
    "kbd",
    "label",
    "link",  # if 'itemprop' attribute is present
    "map",  # if it contains only phrasing content
    "mark",
    "math",
    "meta",  # if 'itemprop' attribute is present
    "meter",
    "noscript",
    "object",
    "output",
    "picture",
    "progress",
    "q",
    "ruby",
    "s",
    "samp",
    "script",
    "select",
    "slot",
    "small",
    "span",
    "strong",
    "sub",
    "sup",
    "svg",
    "template",
    "textarea",
    "time",
    "u",
    "var",
    "video",
    "wbr",
    # obsolete
    "command",
    # deprecated
    "keygen",
]

EMBEDDED_TAGS = [  # https://html.spec.whatwg.org/multipage/dom.html#embedded-content-category
    "audio",
    "canvas",
    "embed",
    "iframe",
    "img",
    "math",
    "object",
    "picture",
    "svg",
    "video",
]

INTERACTIVE_TAGS = [  # https://html.spec.whatwg.org/multipage/dom.html#interactive-content-2
    "a",  # if the 'href' attribute is present
    "audio",  # if the 'controls' attribute is present
    "button",
    "details",
    "embed",
    "iframe",
    "img",  # if the 'usemap' attribute is present
    "input",  # if the 'type' attribute is not in the hidden state
    "label",
    "object",  # if the 'usemap' attribute is present
    "select",
    "textarea",
    "video",  # if the 'controls' attribute is present
]


RUBY_TAGS = [
    "rb",
    "rp",
    "rt",
    "rtc",
    "ruby",
]


MARKUP_TAGS = [
    # Inline text semantics
    # (except <a>, <time>, and single-sided tags: <wbr>)
    "abbr",
    "b",
    "bdi",
    "bdo",
    "cite",
    "code",
    "data",
    "dfn",
    "em",
    "i",
    "kbd",
    "mark",
    "q",
    "rb",
    "rp",
    "rt",
    "rtc",
    "ruby",
    "s",
    "samp",
    "small",
    "strong",
    "sub",
    "sup",
    "u",
    "var",
    # Demarcating edits (all)
    "del",
    "ins",
]


# tags to decompose in first cleaning (before extracting assets)
KILL_TAGS = [
    # Document metadata (selected)
    "style",
    # Scripting (all)
    "canvas",
    "noscript",
    "script",
    # Interactive elements (all)
    "details",
    "dialog",
    "menu",
    "summary",
    # Web Components (all)
    "slot",
    "template",
]

IMAGE_AND_MULTIMEDIA_TAGS = [
    "area",
    "audio",
    "img",
    "map",
    "track",
    "video",
]

EMBEDDED_CONTENT_TAGS = [
    "embed",
    "iframe",
    "object",
    "param",
    "picture",
    "source",
]

DECOMPOSE_TAGS = [
    # Document metadata (selected)
    "style",
    # Content sectioning (selected)
    "aside",
    "nav",
    # # Image and multimedia (all)
    # "area", "audio", "img", "map", "track", "video",
    # # Embedded content (all)
    # "embed", "iframe", "object", "param", "picture", "source",
    # Scripting (all)
    "canvas",
    "noscript",
    "script",
    # Tables (all)
    "caption",
    "col",
    "colgroup",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    # Forms (all) # except "form"; some websites poorly format and put everything in <form>
    "button",
    "datalist",
    "fieldset",
    "input",
    "label",
    "legend",
    "meter",
    "optgroup",
    "option",
    "output",
    "progress",
    "select",
    "textarea",
    # Interactive elements (all)
    "details",
    "dialog",
    "menu",
    "summary",
    # Web Components (all)
    "slot",
    "template",
]

HARD_TAGS = [
    # Sectioning root
    "body",
    # Content sectioning (selected)
    "address",
    "article",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hgroup",
    "main",
    "section",
    # Text content (selected)
    "div",
    "dl",
    "figure",
    "ol",
    "p",
    "ul",
    # Inline text semantics
    "span",
    "time",
]


IFRAME_SRC_LIST = [
    "google",  # 1
    "youtube",  # 2
    "facebook",  # 6
    "okezone",  # 22
    "instagram",  # 25
    "twitch",  # 34
    "twitter",  # 45
    "wordpress",
    "wp",  # 59
    "spotify",  # 84
    "detik",  # 97
    "tiktok",  # 148
    "sindonews",  # 149
    "vimeo",  # 173
    "dailymotion",  # 256
    "blogger",  # 277
    "outbrain",  # 449
    "giphy",  # 606
    "republika",  # 796
    "getpocket",  # 859
    "disqus",  # 974
    "rctiplus",  # 1874
    "straitstimes",  # 4742
    "dable",  # 5434
    "sharethis" "brightcove",  # 9585  # 11272
    "datawrapper",  # 38453
    "omny",  # 53254
    "embedly",  # 91842
    "vidible",  # 98248
    "ustream",  # 114362
    "graphicnews",  # 227295
]

IFRAME_SRC_IGNORELIST = [
    "javascript:void(0)",
    "about:blank",
]

IFRAME_SRCPARSE_IGNORELIST = [
    ["draft.blogger.com", "/navbar.g"],
    ["www.blogger.com", "/navbar.g"],
    ["api.dable.io", r"/widgets/id/[a-zA-Z0-9]{8}/users/\d+\.\d+"],
    ["widgets.getpocket.com", "/v1/button"],
    ["vastcdn.outbrain.com", "/frame"],
    ["embed.rctiplus.com", "/newswidget/okezone"],
    ["republika.co.id", "/jadwal-sholat/"],
    ["ws.sharethis.com", "/secure5x/index.html"],
    ["index.sindonews.com", "/widget"],
]

IFRAME_SRC_ASSETS = {
    "google": {
        r"apis\.google\.com": {
            r"\/se\/0\/_\/\+1\/fastbutton": "ignore",
            r"\/se\/0\/_\/\+1\/sharebutton": "ignore",
        },
        r"docs\.google\.com": {
            r"\/document\/d\/e\/[a-zA-Z0-9_-]+\/pub": "links",
            r"\/forms\/d\/e\/[a-zA-Z0-9_-]+\/viewform": "links",
            r"\/spreadsheets\/d\/e\/[a-zA-Z0-9_-]+\/pubhtml": "links",
            r"\/presentation\/d\/e\/[a-zA-Z0-9_-]+\/embedded": "links",
        },
        r"drive\.google\.com": {
            r"\/file\/d\/[a-zA-Z0-9_-]\/preview": "links",  # could be photo / video / something else
        },
        r"googleads\.g\.doubleclick\.net": {
            r"\/pagead\/ads": "ignore",
            r"\/pagead\/html\/.+\.html": "ignore",
            r"\/pagead\/render_post_image_v1\.html": "ignore",
        },
        r"imasdk\.googleapis\.com": {
            r"\/js\/core\/bridge[\d.]+_en\.html": "ignore",
        },
        r"tpc\.googlesyndication\.com": {
            r"\/safeframe\/1-0-37\/html\/container\.html": "ignore",
        },
        r"[0-9a-f]+\.safeframe\.googlesyndication\.com": {
            r"\/safeframe\/1-0-37\/html\/container\.html": "ignore",
        },
        r"www\.google\.com": {
            r"\/maps\/embed": "links",
            r"\/recaptcha\/api\/fallback": "ignore",
            r"\/recaptcha\/api2\/anchor": "ignore",
            r"\/recaptcha\/api2\/bframe": "ignore",
        },
    },
    "youtube": {  # https://developers.google.com/youtube/player_parameters#Manual_IFrame_Embeds
        r"www\.youtube\.com": {
            r"\/embed\/[a-zA-Z0-9_-]+": "video",  # Embedded Video
            r"\/embed\/?": "video",  # Playlist
            r"\/watch": "video",  # Video
            r"\/subscribe_embed": "ignore",
        },
    },
    "facebook": {  # https://developers.facebook.com/docs/plugins
        r"www\.facebook\.com": {
            # Embedded Videos
            # https://developers.facebook.com/docs/plugins/embedded-video-player
            r"\/(v\d+\.\d+\/)?plugins\/video\.php": "video",
            # Comments: (note: embedding in <iframe> deprecated)
            # https://developers.facebook.com/docs/plugins/comments
            r"\/(v\d+\.\d+\/)?plugins\/comments\.php": "comments",
            r"\/(v\d+\.\d+\/)?plugins\/feedback\.php": "comments",  # not encountered
            # Embedded Comments:
            # https://developers.facebook.com/docs/plugins/embedded-comments
            r"\/(v\d+\.\d+\/)?plugins\/comment_embed\.php": "links",
            # Embedded Posts:
            # https://developers.facebook.com/docs/plugins/embedded-posts
            r"\/(v\d+\.\d+\/)?plugins\/post\.php": "links",
            # Group Plugin
            # https://developers.facebook.com/docs/plugins/group-plugin
            r"\/(v\d+\.\d+\/)?plugins\/group\.php": "links",  # not encountered
            # Page Plugin
            # https://developers.facebook.com/docs/plugins/page-plugin
            r"\/(v\d+\.\d+\/)?plugins\/page\.php": "links",
            # Like Button
            # https://developers.facebook.com/docs/plugins/like-button
            r"\/(v\d+\.\d+\/)?plugins\/like\.php": "ignore",
            # Like Box (deprecated)
            # https://developers.facebook.com/docs/plugins/like-box-for-pages
            r"\/(v\d+\.\d+\/)?plugins\/like_box\.php": "ignore",  # not encountered
            r"\/plugins\/likebox\.php": "ignore",
            # Quote Plugin: (note: embedding in <iframe> deprecated)
            # https://developers.facebook.com/docs/plugins/quote
            r"\/v\d+\.\d+\/plugins\/quote\.php": "ignore",
            # Save Button (note: embedding in <iframe> deprecated)
            # https://developers.facebook.com/docs/plugins/save
            r"\/(v\d+\.\d+\/)?plugins\/save\.php": "ignore",  # not encountered
            # Share Button
            # https://developers.facebook.com/docs/plugins/share-button
            r"\/v\d+\.\d+\/plugins\/share_button\.php": "ignore",
        },
        r"web\.facebook\.com": {
            # Embedded Videos
            # https://developers.facebook.com/docs/plugins/embedded-video-player
            r"\/v\d+\.\d+\/plugins\/video\.php": "video",  # not encountered
            # Comments: (note: embedding in <iframe> deprecated)
            # https://developers.facebook.com/docs/plugins/comments
            r"\/v\d+\.\d+\/plugins\/comments\.php": "comments",
            r"\/v\d+\.\d+\/plugins\/feedback\.php": "comments",  # not encountered
            # Embedded Comments:
            # https://developers.facebook.com/docs/plugins/embedded-comments
            r"\/v\d+\.\d+\/plugins\/comment_embed\.php": "links",  # not encountered
            # Embedded Posts:
            # https://developers.facebook.com/docs/plugins/embedded-posts
            r"\/v\d+\.\d+\/plugins\/post\.php": "links",
            # Group Plugin
            # https://developers.facebook.com/docs/plugins/group-plugin
            r"\/v\d+\.\d+\/plugins\/group\.php": "links",  # not encountered
            # Page Plugin
            # https://developers.facebook.com/docs/plugins/page-plugin
            r"\/v\d+\.\d+\/plugins\/page\.php": "links",
            # Like Button
            # https://developers.facebook.com/docs/plugins/like-button
            r"\/v\d+\.\d+\/plugins\/like\.php": "ignore",
            # Like Box (deprecated)
            # https://developers.facebook.com/docs/plugins/like-box-for-pages
            r"\/v\d+\.\d+\/plugins\/like_box\.php": "ignore",  # not encountered
            r"\/v\d+\.\d+\/plugins\/likebox\.php": "ignore",  # not encountered
            # Quote Plugin: (note: embedding in <iframe> deprecated)
            # https://developers.facebook.com/docs/plugins/quote
            r"\/v\d+\.\d+\/plugins\/quote\.php": "ignore",  # not encountered
            # Save Button (note: embedding in <iframe> deprecated)
            # https://developers.facebook.com/docs/plugins/save
            r"\/v\d+\.\d+\/plugins\/save\.php": "ignore",  # not encountered
            # Share Button
            # https://developers.facebook.com/docs/plugins/share-button
            r"\/v\d+\.\d+\/plugins\/share_button\.php": "ignore",
        },
    },
    "instagram": {  # https://developers.facebook.com/docs/instagram/oembed/
        r"www\.instagram\.com": {
            r"\/tv\/[a-zA-Z0-9_-]+\/embed\/(captioned\/)?": "video",
            r"\/p\/[a-zA-Z0-9_-]+\/embed\/": "links",  # Post
        },
    },
    "okezone": {
        r"video\.okezone\.com": {
            r"\/embed\/.+==": "video",
        },
        r"sindikasi\.okezone\.com": {
            r"\/widget(\/.+)?": "ignore",
        },
        r"okezone\.visionplus\.id": {
            r"\/widget-dark\.html": "ignore",
        },
    },
    "twitch": {  # https://dev.twitch.tv/docs/embed
        r"player\.twitch\.tv": {
            # https://dev.twitch.tv/docs/embed/video-and-clips
            r"\/": "video",  # not encountered
        },
        r"clips\.twitch\.tv": {
            # https://dev.twitch.tv/docs/embed/video-and-clips
            r"\/embed": "video",  # not encountered
        },
        r"www\.twitch\.tv": {
            # https://dev.twitch.tv/docs/embed/chat
            r"\/embed\/[^/]\/chat": "links",  # not encountered
        },
    },
    "twitter": {  # https://developer.twitter.com/en/docs/twitter-for-websites
        r"platform\.twitter\.com": {
            # https://developer.twitter.com/en/docs/twitter-for-websites/embedded-tweets/overview
            r"\/embed\/index\.html": "links",
            r"\/widgets\/tweet_button(\.[0-9a-f]+)?(\.[a-z]+)?\.html": "ignore",
            r"\/widgets\/follow_button(\.[0-9a-f]+)?(\.[a-z]+)?\.html": "ignore",
            r"\/widgets\/widget_iframe(\.[0-9a-f]+)?(\.[a-z]+)?\.html": "ignore",  # not encountered
        },
    },
    "wordpress": {
        r"jetpack\.wordpress\.com": {
            # https://jetpack.com/support/comments/
            r"\/jetpack-comment\/": "comments",
        },
    },
    "wp": {
        r"widgets\.wp\.com": {
            r"\/likes\/": "ignore",
        },
    },
    "spotify": {  # https://developer.spotify.com/documentation/widgets/generate/embed/
        r"open\.spotify\.com": {
            r"\/embed\/track\/": "links",  # Song # not enocuntered
            r"\/embed\/album\/": "links",  # Album # not enocuntered
            r"\/embed\/artist\/": "links",  # Artist # not enocuntered
            r"\/embed\/playlist\/": "links",  # Playlist # not enocuntered
            r"\/embed-podcast\/show\/": "links",  # Podcast # not enocuntered
            r"\/embed-podcast\/episode\/[a-zA-Z0-9_-]+": "links",  # Episode
        },
    },
    "detik": {
        r"20\.detik\.com": {
            r"\/embed\/\d+": "video",
        },
    },
    "tiktok": {  # https://developers.tiktok.com/doc/Embed
        "www.tiktok.com": {
            r"\/embed\/v2": "video",  # does not follow URL
        },
    },
    "vimeo": {  # https://developer.vimeo.com/api/oembed/videos
        r"player\.vimeo\.com": {
            r"\/video\/[\d]+": "video",  # not encountered
        },
    },
    "dailymotion": {  # https://developer.dailymotion.com/player/#player-html
        r"www\.dailymotion\.com": {
            r"\/embed\/video\/[a-zA-Z0-9_-]+": "video",
            # https://faq.dailymotion.com/hc/en-us/articles/360001749507-Sharing-Embedding-Playlists
            r"\/embed\/playlist\/[a-zA-Z0-9_-]+": "video",  # Playlist # not encountered
        },
    },
    "giphy": {  # https://support.giphy.com/hc/en-us/articles/360020330711-How-to-Embed-a-GIF
        r"giphy\.com": {
            r"\/embed\/[a-zA-Z0-9_-]+": "video",
        },
    },
    "disqus": {  # https://blog.disqus.com/how-to-embed-disqus-comments-on-your-website
        r"disqus\.com": {
            r"\/embed\/comments\/": "comments",  # Comments section
            r"\/p\/": "links",  # Embedded comment # not encountered
        },
    },
    "straitstimes": {
        r"www\.straitstimes\.com": {
            r"\/embed\/\d+": "video",
        },
    },
    "brightcove": {
        r"players\.brightcove\.net": {
            r"\/[\d]+\/default_default\/index\.html": "video",
        },
    },
    "datawrapper": {  # https://developer.datawrapper.de/docs/responsive-iframe
        r"datawrapper\.dwcdn\.net": {
            r"\/[a-zA-Z0-9_-]{5}\/1\/": "links",
        },
    },
    "omny": {  # https://help.omnystudio.com/en/collections/79814-sharing-your-audio
        r"omny\.fm": {
            r"\/shows\/[a-zA-Z0-9_-]+\/[a-zA-Z0-9_-]+\/embed": "links",
        },
    },
    "embedly": {
        r"cdn\.embedly\.com": {
            r"\/widgets\/media\.html": "video",
        },
    },
    "vidible": {
        r"delivery\.vidible\.tv": {
            r"\/htmlembed\/pid=[0-9a-f]+\/[0-9a-f]+\.html": "video",
        },
    },
    "ustream": {
        r"www\.ustream\.tv": {
            r"\/embed\/\d+": "video",
        },
    },
    "graphicnews": {  # https://www.graphicnews.com/base/info.php?q=1001&s=GN
        r"apps\.graphicnews\.com": {
            r"\/links\/(en\/)?gn_swf\/iframe\.php": "links",
        },
    },
}


LEFT_NOSPACE_PUNCTUATION = [
    # Controls and Basic Latin
    '"',
    "$",
    "'",
    "(",
    "-",
    "/",
    "[",
    "{",
    # Controls and Latin-1 Supplement
    "\u00a1",  # INVERTED EXCLAMATION MARK
    "\u00a3",  # POUND SIGN
    "\u00a4",  # CURRENCY SIGN
    "\u00a5",  # YEN SIGN
    "\u00ab",  # LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    "\u00bf",  # INVERTED QUESTION MARK
    # General Punctuation
    "\u2010",  # HYPHEN
    "\u2011",  # NON-BREAKING HYPHEN
    "\u2018",  # LEFT SINGLE QUOTATION MARK
    "\u201a",  # SINGLE LOW-9 QUOTATION MARK
    "\u201b",  # SINGLE HIGH-REVERSED-9 QUOTATION MARK
    "\u201c",  # LEFT DOUBLE QUOTATION MARK
    "\u201e",  # DOUBLE LOW-9 QUOTATION MARK
    "\u201f",  # DOUBLE HIGH-REVERSED-9 QUOTATION MARK
    "\u2027",  # HYPHENATION POINT
    "\u2035",  # REVERSED PRIME
    "\u2036",  # REVERSED DOUBLE PRIME
    "\u2037",  # REVERSED TRIPLE PRIME
    "\u2039",  # SINGLE LEFT-POINTING ANGLE QUOTATION MARK
    "\u203b",  # REFERENCE MARK
    # Currency Symbols
    "\u0e3f",  # THAI CURRENCY SYMBOL BAHT
    "\u20a1",  # COLON SIGN
    "\u20a2",  # CRUZEIRO SIGN
    "\u20a3",  # FRENCH FRANC SIGN
    "\u20a4",  # LIRA SIGN
    "\u20a6",  # NAIRA SIGN
    "\u20a9",  # WON SIGN
    "\u20aa",  # NEW SHEQEL SIGN
    "\u20ac",  # EURO SIGN
    "\u20ad",  # KIP SIGN
    "\u20ae",  # TUGRIK SIGN
    "\u20b1",  # PESO SIGN
    "\u20b4",  # HRYVNIA SIGN
    "\u20b5",  # GHANAIAN CEDI
    "\u20b9",  # INDIAN RUPEE
    "\u20ba",  # LIRA SIGN
    "\u20be",  # LARI SIGN
    "\u20bf",  # BITCOIN SIGN
]
RIGHT_NOSPACE_PUNCTUATION = [
    # Controls and Basic Latin
    "!",
    '"',
    "%",
    "'",
    ")",
    "*",
    ",",
    "-",
    ".",
    "/",
    ":",
    ";",
    "?",
    "]",
    "}",
    # Controls and Latin-1 Supplement
    "\u00a2",  # CENT SIGN
    "\u00b0",  # DEGREE SIGN
    "\u00bb",  # RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
    # General Punctuation
    "\u2010",  # HYPHEN
    "\u2011",  # NON-BREAKING HYPHEN
    "\u2019",  # RIGHT SINGLE QUOTATION MARK
    "\u201d",  # RIGHT DOUBLE QUOTATION MARK
    "\u2020",  # DAGGER
    "\u2021",  # DOUBLE DAGGER
    "\u2026",  # HORIZONTAL ELLIPSIS
    "\u2027",  # HYPHENATION POINT
    "\u2030",  # PER MILLE SIGN
    "\u2031",  # PER TEN THOUSAND SIGN
    "\u2032",  # PRIME
    "\u2033",  # DOUBLE PRIME
    "\u2034",  # TRIPLE PRIME
    "\u203a",  # SINGLE RIGHT-POINTING ANGLE QUOTATION MARK
    "\u203c",  # DOUBLE EXCLAMATION MARK
    "\u203d",  # INTERROBANG
    # Currency Symbols
    "\u20a5",  # MILL SIGN
    "\u20ab",  # DONG SIGN
    "\u20b0",  # GERMAN PENNY SIGN
    "\u20b2",  # GUARANI SIGN
    "\u20bb",  # MANAT SIGN
    "\u20bc",  # RUBLE SIGN
]