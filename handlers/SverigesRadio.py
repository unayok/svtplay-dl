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
    if "sverigesradio.se" in url :
        return get(url, options)
    return False

def get(url, options):
    data = get_http_data(url)
    parse = urlparse(url)
    try:
        metafile = parse_qs(parse[4])["metafile"][0]
        options.other = "%s?%s" % (parse[2], parse[4])
    except KeyError:
        match = re.search("linkUrl=(.*)\;isButton=", data)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        options.other = unquote_plus(match.group(1))
    url = "http://sverigesradio.se%s" % options.other
    data = get_http_data(url)
    xml = ET.XML(data)
    url = xml.find("entry").find("ref").attrib["href"]
    download_http(options, url)
    return True
