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

def handle_url(url, output):
    if "etv.err.ee" in url :
        return get(url, options)
    return False

def get(url, options):
    data = get_http_data(url)
    match = re.search(r"loadFlow\(.*'(rtmp:[^']*)'.*'(mp4:[^']*)'", data)
    try:
        r = match.group(1)
        y = match.group(2)
    except AttributeError :
        log.error("Could not find video source")
        sys.exit(2)
    else :
        # live appears necessary here, at least for my local version of rtmpdump
        options.other = "-v -y '%s'" % y
        download_rtmp(options,r)
    return True
