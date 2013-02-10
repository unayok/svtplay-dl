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
    if "hbo.com" in url :
        return get(url, options)
    return False

def get(url, options):
    parse = urlparse(url)
    try:
        other = parse[5]
    except KeyError:
        log.error("Something wrong with that url")
        sys.exit(2)
    match = re.search("^/(.*).html", other)
    if not match:
        log.error("Cant find video file")
        sys.exit(2)
    url = "http://www.hbo.com/data/content/%s.xml" % match.group(1)
    data = get_http_data(url)
    xml = ET.XML(data)
    videoid = xml.find("content")[1].find("videoId").text
    url = "http://render.cdn.hbo.com/data/content/global/videos/data/%s.xml" % videoid
    data = get_http_data(url)
    xml = ET.XML(data)
    ss = xml.find("videos")
    if sys.version_info < (2, 7):
        sa = list(ss.getiterator("size"))
    else:
        sa = list(ss.iter("size"))
    streams = {}
    for i in sa:
        stream = {}
        stream["path"] = i.find("tv14").find("path").text
        streams[int(i.attrib["width"])] = stream

    test = select_quality(options, streams)

    download_rtmp(options, test["path"])
    return True

