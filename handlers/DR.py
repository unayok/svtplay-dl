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
    if "dr.dk" in url :
        return get(url, options)
    return False

def get(url, options):
    data = get_http_data(url)
    host = re.search(r'rtmpHost:[ ]*"([^"]*)",', data)
    if host :
        host = "-n '%s'" % host.group(1).replace("rtmp://","")
    else :
        host = ""
    match = re.search(r'resource:[ ]*"([^"]*)",', data)
    resource_url = match.group(1)
    resource_data = get_http_data(resource_url)
    resource = json.loads(resource_data)
    streams = {}
    for stream in resource['links']:
        streams[stream['bitrateKbps']] = stream['uri']
    if len(streams) == 1:
        uri = streams[list(streams.keys())[0]]
    else:
        uri = select_quality(options, streams)
    # need -v ?
    options.other = host + " -v -y '" + uri.replace("rtmp://vod.dr.dk/cms/", "") + "'"
    download_rtmp(options, uri)
    return True
