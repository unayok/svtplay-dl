#!/usr/bin/env python
import sys
if sys.version_info > (3, 0):
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlparse, parse_qs, unquote_plus, quote_plus
    from io import StringIO
else:
    from urllib2 import Request, urlopen, HTTPError, URLError
    from urlparse import urlparse, parse_qs
    from urllib import unquote_plus, quote_plus
    import StringIO

import re
import os
import subprocess
from optparse import OptionParser
import xml.etree.ElementTree as ET
import shlex
import json
import time
import logging
import base64
import struct
import binascii
from sites import *
from utils import *

__version__ = "0.8.2012.12.23"

class Options:
    """
    Options used when invoking the script from another Python script.
    
    Simple container class used when calling get_media() from another Python
    script. The variables corresponds to the command line parameters parsed
    in main() when the script is called directly.
    
    When called from a script there are a few more things to consider:
    
    * Logging is done to 'log'. main() calls setup_log() which sets the
      logging to either stdout or stderr depending on the silent level.
      A user calling get_media() directly can either also use setup_log()
      or configure the log manually.

    * Progress information is printed to 'progress_stream' which defaults to
      sys.stderr but can be changed to any stream.
    
    * Many errors results in calls to system.exit() so catch 'SystemExit'-
      Exceptions to prevent the entire application from exiting if that happens.
    
    """

    def __init__(self):
        self.output = None
        self.resume = False
        self.live = False
        self.silent = False
        self.quality = None
        self.hls = False
        self.other = None

log = logging.getLogger('svtplay_dl')
progress_stream = sys.stderr

def get_media(url, options):
    output = options.output
    live = options.live
    resume = options.resume
    silent = options.silent
    hls = options.hls

    if not options.output or os.path.isdir(options.output):
        data = get_http_data(url)
        match = re.search("(?i)<title>\s*(.*?)\s*</title>", data)
        if match:
            if sys.version_info > (3, 0):
                title = re.sub('[^\w\s-]', '', match.group(1)).strip().lower()
                if output:
                    options.output = options.output + re.sub('[-\s]+', '-', title)
                else:
                    options.output = re.sub('[-\s]+', '-', title)
            else:
                title = unicode(re.sub('[^\w\s-]', '', match.group(1)).strip().lower())
                if options.output:
                    options.output = unicode(options.output + re.sub('[-\s]+', '-', title))
                else:
                    options.output = unicode(re.sub('[-\s]+', '-', title))

    if re.findall("(twitch|justin).tv", url):
        parse = urlparse(url)
        match = re.search("/b/(\d+)", parse.path)
        if match:
            url = "http://api.justin.tv/api/broadcast/by_archive/%s.xml?onsite=true" % match.group(1)
            Justin2().get(options, url)
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
                Justin().get(options, url)

    if re.findall("hbo.com", url):
        parse = urlparse(url)
        try:
            other = parse[5]
        except KeyError:
            log.error("Something wrong with that url")
            sys.exit(2)
        match = re.search("^/(.*).html", other)
        if not match:
            log.error("Cant find video file")
            sys.exit(2)
        url = "http://www.hbo.com/data/content/" + match.group(1) + ".xml"
        Hbo().get(options, url)

    if re.findall("tv4play", url):
        parse = urlparse(url)
        try:
            vid = parse_qs(parse[4])["video_id"][0]
        except KeyError:
            log.error("Can't find video file")
            sys.exit(2)
        url = "http://premium.tv4play.se/api/web/asset/%s/play" % vid
        Tv4play().get(options, url)

    elif re.findall("(tv3play|tv6play|tv8play)", url):
        parse = urlparse(url)
        match = re.search('\/play\/(.*)/?', parse.path)
        if not match:
            log.error("Cant find video file")
            sys.exit(2)
        url = "http://viastream.viasat.tv/PlayProduct/%s" % match.group(1)
        Viaplay().get(options, url)

    elif re.findall("viaplay", url):
        parse = urlparse(url)
        match = re.search('\/Tv/channels\/[a-zA-Z0-9-]+\/[a-zA-Z0-9-]+\/[a-zA-Z0-9-]+\/(.*)/', parse.path)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        url = "http://viasat.web.entriq.net/nw/article/view/%s/?tf=players/TV6.tpl" % match.group(1)
        data = get_http_data(url)
        match = re.search("id:'(.*)'", data)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        url = "http://viastream.viasat.tv/PlayProduct/%s" % match.group(1)
        Viaplay().get(options, url)

    elif re.findall("aftonbladet", url):
        parse = urlparse(url)
        data = get_http_data(url)
        match = re.search("abTvArticlePlayer-player-(.*)-[0-9]+-[0-9]+-clickOverlay", data)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        try:
            start = parse_qs(parse[4])["start"][0]
        except KeyError:
            start = 0
        url = "http://www.aftonbladet.se/resource/webbtv/article/%s/player" % match.group(1)
        Aftonbladet().get(options, url, start)

    elif re.findall("expressen", url):
        parse = urlparse(url)
        match = re.search("/(.*[\/\+].*)/", unquote_plus(parse.path))
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        url = "http://tv.expressen.se/%s/?standAlone=true&output=xml" % quote_plus(match.group(1))
        Expressen().get(options, url)

    elif re.findall("kanal5play", url):
        match = re.search(".*video/([0-9]+)", url)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        url = "http://www.kanal5play.se/api/getVideo?format=FLASH&videoId=%s" % match.group(1)
        Kanal5().get(options, url)


    elif re.findall("kanal9play", url):
        data = get_http_data(url)
        match = re.search("@videoPlayer\" value=\"(.*)\"", data)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        Kanal9().get(options, "c.brightcove.com")

    elif re.findall("dn.se", url):
        data = get_http_data(url)
        match = re.search("data-qbrick-mcid=\"([0-9A-F]+)\"", data)
        if not match:
            match = re.search("mediaId = \'([0-9A-F]+)\';", data)
            if not match:
                log.error("Can't find video file")
                sys.exit(2)
            mcid = match.group(1) + "DE1BA107"
        else:
            mcid = match.group(1)
        host = "http://vms.api.qbrick.com/rest/v3/getsingleplayer/" + mcid
        data = get_http_data(host)
        xml = ET.XML(data)
        try:
            url = xml.find("media").find("item").find("playlist").find("stream").find("format").find("substream").text
        except AttributeError:
            log.error("Can't find video file")
            sys.exit(2)
        Qbrick().get(options, url)

    elif re.findall("di.se", url):
        data = get_http_data(url)
        match = re.search("ccid: \"(.*)\"\,", data)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)
        host = "http://vms.api.qbrick.com/rest/v3/getplayer/" + match.group(1)
        data = get_http_data(host)
        xml = ET.XML(data)
        try:
            host = xml.find("media").find("item").find("playlist").find("stream").find("format").find("substream").text
        except AttributeError:
            log.error("Can't find stream")
            sys.exit(2)
        Qbrick().get(options, host)

    elif re.findall("svd.se", url):
        match = re.search("_([0-9]+)\.svd", url)
        if not match:
            log.error("Can't find video file")
            sys.exit(2)

        data = get_http_data("http://www.svd.se/?service=ajax&type=webTvClip&articleId=" + match.group(1))
        match = re.search("mcid=([A-F0-9]+)\&width=", data)

        if not match:
            log.error("Can't find video file")
            sys.exit(2)

        host = "http://vms.api.qbrick.com/rest/v3/getsingleplayer/" + match.group(1)
        data = get_http_data(host)
        xml = ET.XML(data)
        try:
            host = xml.find("media").find("item").find("playlist").find("stream").find("format").find("substream").text
        except AttributeError:
            log.error("Can't find video file")
            sys.exit(2)
        Qbrick().get(options, host)

    elif re.findall("urplay.se", url):
        Urplay().get(options, url)

    elif re.findall("sverigesradio", url):
        data = get_http_data(url)
        parse = urlparse(url)
        try:
            metafile = parse_qs(parse[4])["metafile"][0]
            other = "%s?%s" % (parse[2], parse[4])
        except KeyError:
            match = re.search("linkUrl=(.*)\;isButton=", data)
            if not match:
                log.error("Can't find video file")
                sys.exit(2)
            other = unquote_plus(match.group(1))
        Sr().get(options, "http://sverigesradio.se")

    elif re.findall("svt.se", url):
        data = get_http_data(url)
        match = re.search("data-json-href=\"(.*)\"", data)
        if match:
            filename = match.group(1).replace("&amp;", "&").replace("&format=json", "")
            url = "http://www.svt.se%s" % filename
        else:
            log.error("Can't find video file")
            sys.exit(2)
        Svtplay().get(options, url)

    elif re.findall("svtplay.se", url):
        Svtplay().get(options, url)
    else:
        log.error("That site is not supported. Make a ticket or send a message")
        sys.exit(2)

def setup_log(silent):
    if silent:
        stream = sys.stderr
        level = logging.WARNING
    else:
        stream = sys.stdout
        level = logging.INFO
        
    fmt = logging.Formatter('%(levelname)s %(message)s')
    hdlr = logging.StreamHandler(stream)
    hdlr.setFormatter(fmt)

    log.addHandler(hdlr)
    log.setLevel(level)

def main():
    """ Main program """
    usage = "usage: %prog [options] url"
    parser = OptionParser(usage=usage, version=__version__)
    parser.add_option("-o", "--output",
        metavar="OUTPUT", help="Outputs to the given filename.")
    parser.add_option("-r", "--resume",
        action="store_true", dest="resume", default=False,
        help="Resume a download")
    parser.add_option("-l", "--live",
        action="store_true", dest="live", default=False,
        help="Enable for live streams")
    parser.add_option("-s", "--silent",
        action="store_true", dest="silent", default=False)
    parser.add_option("-q", "--quality",
        metavar="quality", help="Choose what format to download.\nIt will download the best format by default")
    parser.add_option("-H", "--hls",
        action="store_true", dest="hls", default=False)
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")

    setup_log(options.silent)

    url = args[0]
    get_media(url, options)

if __name__ == "__main__":
    main()
