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
    if ("dn.se" in url) or ("di.se" in url) or ("svd.se" in url) :
        return get(url, options)

def get(url, options):
    if re.findall("dn.se", url):
        data = get_http_data(url)
        match = re.search("data-qbrick-mcid=\"([0-9A-F]+)\"", data)
        if not match:
            match = re.search("mediaId = \'([0-9A-F]+)\';", data)
            if not match:
                log.error("Can't find video file")
                sys.exit(2)
            mcid = "%sDE1BA107" % match.group(1)
        else:
            mcid = match.group(1)
        host = "http://vms.api.qbrick.com/rest/v3/getsingleplayer/%s" % mcid
    elif re.findall("di.se", url):
        data = get_http_data(url)
        match = re.search("ccid: \"(.*)\"\,", data)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        host = "http://vms.api.qbrick.com/rest/v3/getplayer/%s" % match.group(1)
    elif re.findall("svd.se", url):
        match = re.search("_([0-9]+)\.svd", url)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        data = get_http_data("http://www.svd.se/?service=ajax&type=webTvClip&articleId=%s" % match.group(1))
        match = re.search("mcid=([A-F0-9]+)\&width=", data)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        host = "http://vms.api.qbrick.com/rest/v3/getsingleplayer/%s" % match.group(1)
    else:
        log.error("Can't find site")
        sys.exit(2)

    data = get_http_data(host)
    xml = ET.XML(data)
    try:
        url = xml.find("media").find("item").find("playlist").find("stream").find("format").find("substream").text
    except AttributeError:
        log.error("Can't find video file")
        sys.exit(2)

    data = get_http_data(url)
    xml = ET.XML(data)
    server = xml.find("head").find("meta").attrib["base"]
    streams = xml.find("body").find("switch")
    if sys.version_info < (2, 7):
        sa = list(streams.getiterator("video"))
    else:
        sa = list(streams.iter("video"))
    streams = {}
    for i in sa:
        streams[int(i.attrib["system-bitrate"])] = i.attrib["src"]

    path = select_quality(options, streams)

    options.other = "-y %s" % path
    download_rtmp(options, server)
    return True
