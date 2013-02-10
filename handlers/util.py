import sys
if sys.version_info > (3, 0):
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlparse, parse_qs, unquote_plus, quote_plus
    from io import BytesIO as StringIO
else:
    from urllib2 import Request, urlopen, HTTPError, URLError
    from urlparse import urlparse, parse_qs
    from urllib import unquote_plus, quote_plus
    from StringIO import StringIO

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
from datetime import timedelta
import logging

log = logging.getLogger("svtplay_dl")


def readbyte(data, pos):
    return struct.unpack("B", data[pos])[0]

def read16(data, pos):
    endpos = pos + 2
    return struct.unpack(">H", data[pos:endpos])[0]

def read24(data, pos):
    end = pos + 3
    return struct.unpack(">L", "\x00" + data[pos:end])[0]

def read32(data, pos):
    end = pos + 4
    return struct.unpack(">i", data[pos:end])[0]

def read64(data, pos):
    end = pos + 8
    return struct.unpack(">Q", data[pos:end])[0]

def readstring(data, pos):
    length = 0
    while (data[pos + length] != "\x00"):
        length += 1
    endpos = pos + length
    string = data[pos:endpos]
    pos += length + 1
    return pos, string

def readboxtype(data, pos):
    boxsize = read32(data, pos)
    tpos = pos + 4
    endpos = tpos + 4
    boxtype = data[tpos:endpos]
    if boxsize > 1:
        boxsize -= 8
        pos += 8
        return pos, boxsize, boxtype

def readbox(data, pos):
    version = readbyte(data, pos)
    pos += 1
    flags = read24(data, pos)
    pos += 3
    bootstrapversion = read32(data, pos)
    pos += 4
    byte = readbyte(data, pos)
    pos += 1
    profile = (byte & 0xC0) >> 6
    live = (byte & 0x20) >> 5
    update = (byte & 0x10) >> 4
    timescale = read32(data, pos)
    pos += 4
    currentmediatime = read64(data, pos)
    pos += 8
    smptetimecodeoffset = read64(data, pos)
    pos += 8
    temp = readstring(data, pos)
    movieidentifier = temp[1]
    pos = temp[0]
    serverentrycount = readbyte(data, pos)
    pos += 1
    serverentrytable = []
    i = 0
    while i < serverentrycount:
        temp = readstring(data, pos)
        serverentrytable.append(temp[1])
        pos = temp[0]
        i += 1
    qualityentrycount = readbyte(data, pos)
    pos += 1
    qualityentrytable = []
    i = 0
    while i < qualityentrycount:
        temp = readstring(data, pos)
        qualityentrytable.append(temp[1])
        pos = temp[0]
        i += 1

    tmp = readstring(data, pos)
    drm = tmp[1]
    pos = tmp[0]
    tmp = readstring(data, pos)
    metadata = tmp[1]
    pos = tmp[0]
    segmentruntable = readbyte(data, pos)
    pos += 1
    if segmentruntable > 0:
        tmp = readboxtype(data, pos)
        boxtype = tmp[2]
        boxsize = tmp[1]
        pos = tmp[0]
        if boxtype == "asrt":
            antal = readasrtbox(data, pos)
            pos += boxsize
    fragRunTableCount = readbyte(data, pos)
    pos += 1
    i = 0
    fragruntables = []
    while i < fragRunTableCount:
        tmp = readboxtype(data, pos)
        boxtype = tmp[2]
        boxsize = tmp[1]
        pos = tmp[0]
        if boxtype == "afrt":
            frt = readafrtbox(data, pos)
            pos += boxsize
        i += 1
        fragruntables.append(frt)
    antal['fragruntables'] = fragruntables
    return antal

def readafrtbox(data, pos):
    box = {}
    box['version'] = readbyte(data, pos)
    pos += 1
    box['flags'] = read24(data, pos)
    pos += 3
    box['timescale'] = read32(data, pos)
    pos += 4
    qualityentry = readbyte(data, pos)
    box['qualityentry'] = qualityentry
    pos += 1
    i = 0
    while i < qualityentry:
        temp = readstring(data, pos)
        qualitysegmulti = temp[1]
        pos = temp[0]
        i += 1
    fragrunentrycount = read32(data, pos)
    box['fragrunentrycount'] = fragrunentrycount
    pos += 4
    i = 0
    fragruns = []
    box['fragruns'] = fragruns
    while i < fragrunentrycount:
        firstfragment = read32(data, pos)
        pos += 4
        timestamp = read64(data, pos)
        pos += 8
        duration = read32(data, pos)
        pos += 4
        i += 1
        fragruns.append((firstfragment, timestamp, duration))
    return box

def readasrtbox(data, pos):
    version = readbyte(data, pos)
    pos += 1
    flags = read24(data, pos)
    pos += 3
    qualityentrycount = readbyte(data, pos)
    pos += 1
    qualitysegmentmodifers = []
    i = 0
    while i < qualityentrycount:
        temp = readstring(data, pos)
        qualitysegmentmodifers.append(temp[1])
        pos = temp[0]
        i += 1

    seqCount = read32(data, pos)
    pos += 4
    ret = {}
    i = 0

    while i < seqCount:
        firstseg = read32(data, pos)
        pos += 4
        fragPerSeg = read32(data, pos)
        pos += 4
        tmp = i + 1
        ret[tmp] = {"first": firstseg, "total": fragPerSeg}
        i += 1
    return ret

def parsem3u(data):
    if not data.startswith("#EXTM3U"):
        raise ValueError("Does not apprear to be a ext m3u file")

    files = []
    streaminfo = {}
    globdata = {}

    data = data.replace("\r", "\n")
    for l in data.split("\n")[1:]:
        if not l:
            continue
        if l.startswith("#EXT-X-STREAM-INF:"):
            #not a proper parser
            info = [x.strip().split("=", 1) for x in l[18:].split(",")]
            streaminfo.update({info[1][0]: info[1][1]})
        elif l.startswith("#EXT-X-ENDLIST"):
            break
        elif l.startswith("#EXT-X-"):
            globdata.update(dict([l[7:].strip().split(":", 1)]))
        elif l.startswith("#EXTINF:"):
            dur, title = l[8:].strip().split(",", 1)
            streaminfo['duration'] = dur
            streaminfo['title'] = title
        elif l[0] == '#':
            pass
        else:
            files.append((l, streaminfo))
            streaminfo = {}

    return globdata, files

def decode_f4f(fragID, fragData):
    start = fragData.find("mdat") + 4
    if (fragID > 1):
        for dummy in range(2):
            tagLen, = struct.unpack_from(">L", fragData, start)
            tagLen &= 0x00ffffff
            start  += tagLen + 11 + 4
    return start

def get_http_data(url, method="GET", header="", data=""):
    """ Get the page to parse it for streams """
    request = Request(url)
    request.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')

    if len(header) > 0:
        request.add_header('Content-Type', header)
    if len(data) > 0:
        request.add_data(data)
    try:
        response = urlopen(request)
    except HTTPError as e:
        log.error("Something wrong with url " + url )
        log.error("Error code: %s" % e.code)
        sys.exit(5)
    except URLError as e:
        log.error("Something wrong with url " + url )
        log.error("Error code: %s" % e.reason)
        sys.exit(5)
    except ValueError as e:
        log.error("Try adding http:// before the url " + url )
        sys.exit(5)
    if sys.version_info > (3, 0):
        data = response.read()
        try:
            data = data.decode("utf-8")
        except UnicodeDecodeError:
            pass
    else:
        try:
            data = response.read()
        except socket.error as e:
            log.error("Lost the connection to the server")
            sys.exit(5)
    response.close()
    return data

def download_hds(options, url, swf=None):
    data = get_http_data(url)
    streams = {}
    bootstrap = {}
    xml = ET.XML(data)
    prefix = xml.find("{http://ns.adobe.com/f4m/1.0}id").text

    if sys.version_info < (2, 7):
        bootstrapIter = xml.getiterator("{http://ns.adobe.com/f4m/1.0}bootstrapInfo")
        mediaIter = xml.getiterator("{http://ns.adobe.com/f4m/1.0}media")
    else:
        bootstrapIter = xml.iter("{http://ns.adobe.com/f4m/1.0}bootstrapInfo")
        mediaIter = xml.iter("{http://ns.adobe.com/f4m/1.0}media")

    for i in bootstrapIter:
        bootstrap[i.attrib["id"]] = i.text

    for i in mediaIter:
        streams[int(i.attrib["bitrate"])] = {"url": i.attrib["url"], "bootstrapInfoId": i.attrib["bootstrapInfoId"], "metadata": i.find("{http://ns.adobe.com/f4m/1.0}metadata").text}

    log.debug("bitrates available: " + str(streams.keys()))

    test = select_quality(options, streams)

    bootstrap = base64.b64decode(bootstrap[test["bootstrapInfoId"]])
    box = readboxtype(bootstrap, 0)
    if box[2] == "abst":
        antal = readbox(bootstrap, box[0])

    baseurl = url[0:url.rfind("/")]

    if options.output != "-":
        extension = re.search("(\.[a-z0-9]+)$", options.output)
        if not extension:
            options.output = "%s.flv" % options.output
        log.info("Outfile: %s", options.output)
        file_d = open(options.output, "wb")
    else:
        file_d = sys.stdout

    file_d.write(binascii.a2b_hex(b"464c56010500000009000000001200010c00000000000000"))
    file_d.write(base64.b64decode(test["metadata"]))
    file_d.write(binascii.a2b_hex(b"00000000"))
    total = antal[1]["total"]
    start = time.time()
    estimated = ""
    i = 1
    try :
        offset = antal["fragruntables"][0]["fragruns"][0][0] - 1
    except KeyError :
        offset = 0
    while i <= total:
        url = "%s/%sSeg1-Frag%s" % (baseurl, test["url"], i + offset)
        if options.output != "-":
            options.progressbar(total, i, estimated)
        data = get_http_data(url)
        number = decode_f4f(i, data)
        file_d.write(data[number:])
        now = time.time()
        dt = now - start
        et = dt / (i + 1) * total
        rt = et - dt
        td = timedelta(seconds = int(rt))
        estimated = "Estimated Remaining: " + str(td)
        i += 1

    if options.output != "-":
        file_d.close()

def download_hls(options, url, baseurl=None):
    data = get_http_data(url)
    globaldata, files = parsem3u(data)
    streams = {}
    for i in files:
        streams[int(i[1]["BANDWIDTH"])] = i[0]

    test = select_quality(options, streams)
    m3u8 = get_http_data(test)
    globaldata, files = parsem3u(m3u8)
    encrypted = False
    key = None
    try:
        keydata = globaldata["KEY"]
        encrypted = True
    except:
        pass

    if encrypted:
        try:
            from Crypto.Cipher import AES
        except ImportError:
            log.error("You need to install pycrypto to download encrypted HLS streams")
            sys.exit(2)
        match = re.search("URI=\"(http://.*)\"", keydata)
        key = get_http_data(match.group(1))
        rand = os.urandom(16)
        decryptor = AES.new(key, AES.MODE_CBC, rand)
    n = 1
    if options.output != "-":
        extension = re.search("(\.[a-z0-9]+)$", options.output)
        if not extension:
            options.output = "%s.ts" % options.output
        log.info("Outfile: %s", options.output)
        file_d = open(options.output, "wb")
    else:
        file_d = sys.stdout

    start = time.time()
    estimated = ""
    for i in files:
        item = i[0]
        if options.output != "-":
            output.progressbar(len(files), n, estimated)
        if item[0:5] != "http:":
            item = "%s/%s" % (baseurl, item)
        data = get_http_data(item)
        if encrypted:
            lots = StringIO(data)

            plain = b""
            crypt = lots.read(1024)
            decrypted = decryptor.decrypt(crypt)
            while decrypted:
                plain += decrypted
                crypt = lots.read(1024)
                decrypted = decryptor.decrypt(crypt)
            data = plain

        file_d.write(data)
        now = time.time()
        dt = now - start
        et = dt / (n + 1) * len(files)
        rt = et - dt
        td = timedelta(seconds = int(rt))
        estimated = "Estimated Remaining: " + str(td)
        n += 1

    if options.output != "-":
        file_d.close()

def download_http(options, url):
    """ Get the stream from HTTP """
    response = urlopen(url)
    total_size = response.info()['Content-Length']
    total_size = int(total_size)
    bytes_so_far = 0
    if options.output != "-":
        extension = re.search("(\.[a-z0-9]+)$", url)
        if extension:
            options.output = options.output + extension.group(1)
        log.info("Outfile: %s", options.output)
        file_d = open(options.output, "wb")
    else:
        file_d = sys.stdout

    lastprogress = 0
    while 1:
        chunk = response.read(8192)
        bytes_so_far += len(chunk)

        if not chunk:
            break

        file_d.write(chunk)
        if options.output != "-":
            now = time.time()
            if lastprogress + 1 < now:
                lastprogress = now
                output.progress(bytes_so_far, total_size)

    if options.output != "-":
        file_d.close()

def download_rtmp(options, url):
    """ Get the stream from RTMP """
    args = []
    if options.live:
        args.append("-v")

    if options.resume:
        args.append("-e")

    extension = re.search("(\.[a-z0-9]+)$", url)
    if options.output != "-":
        if not extension:
            extension = re.search("-y (.+):[-_a-z0-9\/]", options.other)
            if not extension:
                options.output = "%s.flv" % options.output
            else:
                options.output = "%s%s" % (options.output, extension.group(1))
        else:
            options.output = options.output + extension.group(1)
        log.info("Outfile: %s", options.output)
        args += ["-o", options.output]
    if options.silent or options.output == "-":
        args.append("-q")
    if options.other:
        args += shlex.split(options.other)
    command = ["rtmpdump", "-r", url] + args
    try:
        log.debug(str(command))
        subprocess.call(command)
    except OSError as e:
        log.error("Could not execute rtmpdump: " + e.strerror)

def select_quality(options, streams):
    sort = sorted(streams.keys(), key=int)

    if options.quality:
        quality = options.quality
    else:
        quality = sort.pop()

    try:
        selected = streams[int(quality)]
    except (KeyError, ValueError):
        log.error("Can't find that quality. (Try one of: %s)",
                      ", ".join(map(str, sort)))
        sys.exit(4)

    return selected
