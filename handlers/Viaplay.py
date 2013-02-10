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
    if ("tv3play.se" in url) or ("tv6play.se" in url) or ("tv8play.se" in url) :
        return get(url, options)

def get(url, options):
    parse = urlparse(url)
    match = re.search('\/play\/(.*)/?', parse.path)
    if not match:
        log.error("Cant find video file")
        sys.exit(2)
    url = "http://viastream.viasat.tv/PlayProduct/%s" % match.group(1)
    options.other = ""
    data = get_http_data(url)
    xml = ET.XML(data)
    filename = xml.find("Product").find("Videos").find("Video").find("Url").text

    if filename[:4] == "http":
        data = get_http_data(filename)
        xml = ET.XML(data)
        filename = xml.find("Url").text

    options.other = "-W http://flvplayer.viastream.viasat.tv/play/swf/player110516.swf?rnd=1315434062"
    download_rtmp(options, filename)
    return True
