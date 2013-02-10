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
    if ("svtplay.se" in url) or ("svt.se" in url) :
        return get(url, options)
    return False

def get(url, options):
    if re.findall("svt.se", url):
        data = get_http_data(url)
        match = re.search("data-json-href=\"(.*)\"", data)
        if match:
            filename = match.group(1).replace("&amp;", "&").replace("&format=json", "")
            url = "http://www.svt.se%s" % filename
        else:
            log.error("Can't find video file")
            sys.exit(2)
    url = "%s?type=embed" % url
    data = get_http_data(url)
    match = re.search("value=\"(/(public)?(statiskt)?/swf/video/svtplayer-[0-9\.]+swf)\"", data)
    swf = "http://www.svtplay.se%s" % match.group(1)
    options.other = "-W %s" % swf
    url = "%s&output=json&format=json" % url
    data = json.loads(get_http_data(url))
    options.live = data["video"]["live"]
    streams = {}
    streams2 = {} #hack..
    for i in data["video"]["videoReferences"]:
        if options.hls and i["playerType"] == "ios":
            stream = {}
            stream["url"] = i["url"]
            streams[int(i["bitrate"])] = stream
        elif not options.hls and i["playerType"] == "flash":
            stream = {}
            stream["url"] = i["url"]
            streams[int(i["bitrate"])] = stream
        if options.hls and i["playerType"] == "flash":
            stream = {}
            stream["url"] = i["url"]
            streams2[int(i["bitrate"])] = stream

    if len(streams) == 0 and options.hls:
        test = streams2[0]
        test["url"] = test["url"].replace("/z/", "/i/").replace("manifest.f4m", "master.m3u8")
    elif len(streams) == 0:
        log.error("Can't find any streams.")
        sys.exit(2)
    elif len(streams) == 1:
        test = streams[list(streams.keys())[0]]
    else:
        test = select_quality(options, streams)

    if test["url"][0:4] == "rtmp":
        download_rtmp(options, test["url"])
    elif options.hls:
        download_hls(options, test["url"])
    elif ".f4m" in test["url"]: 
        match = re.search("\/se\/secure\/", test["url"])
        if match:
            log.error("This stream is encrypted. Use --hls option")
            sys.exit(2)
        q = "&" if "?" in test['url'] else "?"
        manifest = "%s%shdcore=2.11.3&g=hejsan" % (test["url"], q)
        download_hds(options, manifest, swf)
    else:
        download_http(options, test["url"])
    return True
