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
    if "kanal5play.se" in url :
        return get(url, options)
    return False

def get(url, options):
    match = re.search(".*video/([0-9]+)", url)
    if not match:
        log.error("Can't find video file")
        sys.exit(2)
    url = "http://www.kanal5play.se/api/getVideo?format=FLASH&videoId=%s" % match.group(1)
    data = json.loads(get_http_data(url))
    options.live = data["isLive"]
    steambaseurl = data["streamBaseUrl"]
    streams = {}

    for i in data["streams"]:
        stream = {}
        stream["source"] = i["source"]
        streams[int(i["bitrate"])] = stream

    test = select_quality(options, streams)

    filename = test["source"]
    match = re.search("^(.*):", filename)
    options.output  = "%s.%s" % (options.output, match.group(1))
    options.other = "-W %s -y %s " % ("http://www.kanal5play.se/flash/StandardPlayer.swf", filename)
    download_rtmp(options, steambaseurl)
    return True
