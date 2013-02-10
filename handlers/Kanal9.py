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
    if ("kanal9play.se" in url) or ("kanal5.se" in url) :
        return get(url, options)
    return False

def get(url, options):
    data = get_http_data(url)
    match = re.search("@videoPlayer\" value=\"(.*)\"", data)
    if not match:
        match = re.search("videoId=(\d+)&player", data)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
    try:
        from pyamf import remoting
    except ImportError:
        log.error("You need to install pyamf to download content from kanal5.se and kanal9play")
        log.error("In debian the package is called python-pyamf")
        sys.exit(2)

    player_id = 811317479001
    publisher_id = 22710239001
    const = "9f79dd85c3703b8674de883265d8c9e606360c2e"
    env = remoting.Envelope(amfVersion=3)
    env.bodies.append(("/1", remoting.Request(target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById", body=[const, player_id, match.group(1), publisher_id], envelope=env)))
    env = str(remoting.encode(env).read())
    url = "http://c.brightcove.com/services/messagebroker/amf?playerKey=AQ~~,AAAABUmivxk~,SnCsFJuhbr0vfwrPJJSL03znlhz-e9bk"
    header = "application/x-amf"
    data = get_http_data(url, "POST", header, env)
    streams = {}

    for i in remoting.decode(data).bodies[0][1].body['renditions']:
        stream = {}
        stream["uri"] = i["defaultURL"]
        streams[i["encodingRate"]] = stream

    test = select_quality(options, streams)

    filename = test["uri"]
    match = re.search("(rtmp[e]{0,1}://.*)\&(.*)$", filename)
    options.other = "-W %s -y %s " % ("http://admin.brightcove.com/viewer/us1.25.04.01.2011-05-24182704/connection/ExternalConnection_2.swf", match.group(2))
    download_rtmp(options, match.group(1))
    return True
