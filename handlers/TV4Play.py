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

def handle_url(url, options) :
    if ("tv4play.se" in url) or ("tv4.se" in url) :
        return get(url, options)
    return False

def get(url, options):
    parse = urlparse(url)
    if "tv4play.se" in url:
        try:
            vid = parse_qs(parse[4])["video_id"][0]
        except KeyError:
            log.error("Can't find video file")
            sys.exit(2)
    else:
        match = re.search("-(\d+)$", url)
        if match:
            vid = match.group(1)
        else:
            data = get_http_data(url)
            match = re.search("\"vid\":\"(\d+)\",", data)
            if match:
                vid = match.group(1)
            else:
                log.error("Can't find video file")
                sys.exit(2)

    url = "http://premium.tv4play.se/api/web/asset/%s/play" % vid
    data = get_http_data(url)
    xml = ET.XML(data)
    ss = xml.find("items")
    if sys.version_info < (2, 7):
        sa = list(ss.getiterator("item"))
    else:
        sa = list(ss.iter("item"))

    if xml.find("live").text:
        if xml.find("live").text != "false":
            options.live = True

    streams = {}

    for i in sa:
        if i.find("mediaFormat").text != "smi":
            stream = {}
            stream["uri"] = i.find("base").text
            stream["path"] = i.find("url").text
            streams[int(i.find("bitrate").text)] = stream
    if len(streams) == 1:
        test = streams[list(streams.keys())[0]]
    else:
        test = select_quality(options, streams)

    swf = "http://www.tv4play.se/flash/tv4playflashlets.swf"
    options.other = "-W %s -y %s" % (swf, test["path"])

    if test["uri"][0:4] == "rtmp":
        download_rtmp(options, test["uri"])
    elif test["uri"][len(test["uri"])-3:len(test["uri"])] == "f4m":
        match = re.search("\/se\/secure\/", test["uri"])
        if match:
            log.error("This stream is encrypted. Use --hls option")
            sys.exit(2)
        manifest = "%s?hdcore=2.8.0&g=hejsan" % test["path"]
        download_hds(options, manifest, swf)
    return True
