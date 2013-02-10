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
    if "urplay.se" in url :
        return get(url, options)
    return False

def get(url, options):
    path = None
    data = get_http_data(url)
    match = re.search('file=(.*)\&plugins', data)
    if match:
        path = "mp%s:%s" % (match.group(1)[-1], match.group(1))
        options.other = "-a ondemand -y %s" % path
        download_rtmp(options, "rtmp://streaming.ur.se/")
    else :
        match = re.search(r'file_flash: "([^"]*mp4)"', data)
        if match :
            path = match.group(1).replace("\\","")
            data = get_http_data("http://130.242.59.74/loadbalancer.json")
            data = json.loads( data )
            url = "rtmp://%s/ondemand/%s" % ( data['redirect'], path )
            options.other = "-v"
            download_rtmp(options, url)
        else :
            log.error("no video path found.")
    return True
