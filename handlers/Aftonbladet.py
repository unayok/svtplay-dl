import sys
if sys.version_info > (3, 0):
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlparse, parse_qs, unquote_plus, quote_plus
else:
    from urllib2 import Request, urlopen, HTTPError, URLError
    from urlparse import urlparse, parse_qs
    from urllib import unquote_plus, quote_plus

import re
import os
import xml.etree.ElementTree as ET
import json
import time
from datetime import timedelta
import logging

log = logging.getLogger("svtplay_dl")

from handlers.util import *

def handle_url(url, options):
    if "aftonbladet.se" in url :
        return get(url, options)
    return False

def get(url, options):
    parse = urlparse(url)
    data = get_http_data(url)
    match = re.search("abTvArticlePlayer-player-(.*)-[0-9]+-[0-9]+-clickOverlay", data)
    if not match:
        log.error("Can't find video file")
        sys.exit(2)
    try:
        start = parse_qs(parse[4])["start"][0]
    except KeyError:
        start = 0
    url = "http://www.aftonbladet.se/resource/webbtv/article/%s/player" % match.group(1)
    data = get_http_data(url)
    xml = ET.XML(data)
    url = xml.find("articleElement").find("mediaElement").find("baseUrl").text
    path = xml.find("articleElement").find("mediaElement").find("media").attrib["url"]
    live = xml.find("articleElement").find("mediaElement").find("isLive").text
    options.other = "-y %s" % path

    if start > 0:
        options.other = "%s -A %s" % (options.other, str(start))

    if live == "true":
        options.live = True

    if url == None:
        log.error("Can't find any video on that page")
        sys.exit(3)

    if url[0:4] == "rtmp":
        download_rtmp(options, url)
    else:
        filename = url + path
        download_http(options, filename)
    return True
