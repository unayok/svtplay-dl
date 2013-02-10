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
    if "ruv.is" in url :
        return get(url, options)
    return False

def get(url, options):
    data = get_http_data(url)
    match = re.search(r'(http://load.cache.is/vodruv.*)"', data)
    js_url = match.group(1)
    js = get_http_data(js_url)
    tengipunktur = js.split('"')[1]
    match = re.search(r"http.*tengipunktur [+] '([:]1935.*)'", data)
    m3u8_url = "http://" + tengipunktur + match.group(1)
    base_url = m3u8_url.rsplit("/", 1)[0]
    download_hls(options, m3u8_url, base_url)
    return True
