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
    if ("twitch.tv" in url) or ("justin.tv" in url) :
        return get(url, options)
    return False

def get(url, options):
    parse = urlparse(url)
    match = re.search("/b/(\d+)", parse.path)
    if match:
        url = "http://api.justin.tv/api/broadcast/by_archive/%s.xml?onsite=true" % match.group(1)
        data = get_http_data(url)
        xml = ET.XML(data)
        url = xml.find("archive").find("video_file_url").text

        download_http(options, url)
    else:
        match = re.search("/(.*)", parse.path)
        if match:
            user = match.group(1)
            data = get_http_data(url)
            match = re.search("embedSWF\(\"(.*)\", \"live", data)
            if not match:
                log.error("Can't find swf file.")
            options.other = match.group(1)
            url = "http://usher.justin.tv/find/%s.xml?type=any&p=2321" % user
            options.live = True
            data = get_http_data(url)
            data = re.sub("<(\d+)", "<_\g<1>", data)
            data = re.sub("</(\d+)", "</_\g<1>", data)
            xml = ET.XML(data)
            if sys.version_info < (2, 7):
                sa = list(xml)
            else:
                sa = list(xml)
            streams = {}
            for i in sa:
                if i.tag[1:][:-1] != "iv":
                    try:
                        stream = {}
                        stream["token"] = i.find("token").text
                        stream["url"] = "%s/%s" % (i.find("connect").text, i.find("play").text)
                        streams[int(i.find("video_height").text)] = stream
                    except AttributeError:
                        pass

            test = select_quality(options, streams)
            options.other = "-j '%s' -W %s" % (test["token"], options.other)
            options.resume = False
            download_rtmp(options, test["url"])
    return True
