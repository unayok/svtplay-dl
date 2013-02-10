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
    if "nrk.no" in url :
        return get(url, options)
    return False

def get(url, options):
    data = get_http_data(url)
    match = re.search(r'data-media="(.*manifest.f4m)"', data)
    manifest_url = match.group(1)
    if options.hls:
        manifest_url = manifest_url.replace("/z/", "/i/").replace("manifest.f4m", "master.m3u8")
        download_hls(options, manifest_url)
    else:
        manifest_url = "%s?hdcore=2.8.0&g=hejsan" % manifest_url
        download_hds(options, manifest_url)
    return True
