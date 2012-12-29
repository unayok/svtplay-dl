import re
import json
from utils import *
from streams.hds import *
from streams.hls import *
from streams.http import *
from streams.rtmp import *

class Justin():
    def get(self, options, url):
        options.other = "-a ondemand"
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
                    stream["url"] = i.find("connect").text + "/" + i.find("play").text
                    streams[int(i.find("video_height").text)] = stream
                except AttributeError:
                    None

        test = select_quality(options, streams)
        options.other = "-j '%s' -W %s" % (test["token"], options.resume)
        options.resume = False
        download_rtmp(options, test["url"], options.output, options.live, options.other, options.resume)

class Justin2():
    def get(self, options, url):
        data = get_http_data(url)
        xml = ET.XML(data)
        url = xml.find("archive").find("video_file_url").text

        download_http(url, options.output)

class Hbo():
    def get(self, url):
        data = get_http_data(url)
        xml = ET.XML(data)
        videoid = xml.find("content")[1].find("videoId").text
        url = "http://render.cdn.hbo.com/data/content/global/videos/data/%s.xml" % videoid
        data = get_http_data(url)
        xml = ET.XML(data)
        ss = xml.find("videos")
        if sys.version_info < (2, 7):
            sa = list(ss.getiterator("size"))
        else:
            sa = list(ss.iter("size"))
        streams = {}
        for i in sa:
            stream = {}
            stream["path"] = i.find("tv14").find("path").text
            streams[int(i.attrib["width"])] = stream

        test = select_quality(options, streams)

        download_rtmp(options, test["path"], options.output, options.live, "", options.resume)

class Sr():
    def get(self, options, url):
        url = url + options.other
        data = get_http_data(url)
        xml = ET.XML(data)
        url = xml.find("entry").find("ref").attrib["href"]

        download_http(url, options.output)

class Urplay():
    def get(self, options, url):
        data = get_http_data(url)
        match = re.search('file=(.*)\&plugins', data)
        if match:
            path = "mp" + match.group(1)[-1] + ":" + match.group(1)
            options.other = "-a ondemand -y %s" % path

            download_rtmp(options, "rtmp://streaming.ur.se/", options.output, options.live, options.other, options.resume)

class Qbrick():
    def get(self, options, url):
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
        download_rtmp(options, server, options.output, options.live, options.other, options.resume)

class Kanal5():
    def get(self, options, url):
        data = json.loads(get_http_data(url))
        self.live = data["isLive"]
        steambaseurl = data["streamBaseUrl"]
        streams = {}

        for i in data["streams"]:
            stream = {}
            stream["source"] = i["source"]
            streams[int(i["bitrate"])] = stream

        test = select_quality(options, streams)

        filename = test["source"]
        match = re.search("^(.*):", filename)
        options.output  = "%s.%s" % (options.output, match.group(1))
        options.other = "-W %s -y %s " % ("http://www.kanal5play.se/flash/StandardPlayer.swf", filename)
        download_rtmp(options, steambaseurl, options.output, options.live, options.other, options.resume)

class Kanal9():
    def get(self, options, url):
        try:
            from pyamf import remoting
        except ImportError:
            log.error("You need to install pyamf to download content from kanal5 and kanal9")
            log.error("In debian the package is called python-pyamf")
            sys.exit(2)

        player_id = 811317479001
        publisher_id = 22710239001
        const = "9f79dd85c3703b8674de883265d8c9e606360c2e"
        env = remoting.Envelope(amfVersion=3)
        env.bodies.append(("/1", remoting.Request(target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById", body=[const, player_id, self.other, publisher_id], envelope=env)))
        env = str(remoting.encode(env).read())
        url = "http://" + url + "/services/messagebroker/amf?playerKey=AQ~~,AAAABUmivxk~,SnCsFJuhbr0vfwrPJJSL03znlhz-e9bk"
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
        download_rtmp(options, match.group(1), options.output, options.live, options.other, options.resume)

class Expressen():
    def get(self, options, url):
        other = ""
        data = get_http_data(url)
        xml = ET.XML(data)
        ss = xml.find("vurls")
        if sys.version_info < (2, 7):
            sa = list(ss.getiterator("vurl"))
        else:
            sa = list(ss.iter("vurl"))
        streams = {}

        for i in sa:
            streams[int(i.attrib["bitrate"])] = i.text

        test = select_quality(options, streams)

        filename = test
        match = re.search("rtmp://([0-9a-z\.]+/[0-9]+/)(.*).flv", filename)

        filename = "rtmp://%s" % match.group(1)
        options.other = "-y %s" % match.group(2)

        download_rtmp(options, filename, options.output, options.live, options.other, options.resume)

class Aftonbladet():
    def get(self, url, start):
        data = get_http_data(url)
        xml = ET.XML(data)
        url = xml.find("articleElement").find("mediaElement").find("baseUrl").text
        path = xml.find("articleElement").find("mediaElement").find("media").attrib["url"]
        options.other = "-y %s" % path

        if start > 0:
            options.other = options.other + " -A %s" % str(start)

        if url == None:
            log.error("Can't find any video on that page")
            sys.exit(3)

        if url[0:4] == "rtmp":
            download_rtmp(options, url, options.output, options.live, options.other, options.resume)
        else:
            filename = url + path
            download_http(filename, options.output)

class Viaplay():
    def get(self, options, url):
        options.other = ""
        data = get_http_data(url)
        xml = ET.XML(data)
        filename = xml.find("Product").find("Videos").find("Video").find("Url").text

        if filename[:4] == "http":
            data = get_http_data(filename)
            xml = ET.XML(data)
            filename = xml.find("Url").text

        options.other = "-W http://flvplayer.viastream.viasat.tv/play/swf/player110516.swf?rnd=1315434062"
        download_rtmp(options, filename, options.output, options.live, options.other, options.resume)

class Tv4play():
    def get(self, options, url):
        data = get_http_data(url)
        xml = ET.XML(data)
        ss = xml.find("items")
        if sys.version_info < (2, 7):
            sa = list(ss.getiterator("item"))
        else:
            sa = list(ss.iter("item"))
        
        if xml.find("live").text:
            self.live = True

        streams = {}
        sa.pop(len(sa)-1)

        for i in sa:
            stream = {}
            stream["uri"] = i.find("base").text
            stream["path"] = i.find("url").text
            streams[int(i.find("bitrate").text)] = stream

        if len(streams) == 1:
            test = streams[streams.keys()[0]]
        else:
            test = select_quality(options, streams)

        swf = "http://www.tv4play.se/flash/tv4playflashlets.swf"
        options.other = "-W %s -y %s" % (swf, test["path"])

        if test["uri"][0:4] == "rtmp":
            download_rtmp(options, test["uri"], options.output, options.live, options.other, options.resume)
        elif test["uri"][len(test["uri"])-3:len(test["uri"])] == "f4m":
            match = re.search("\/se\/secure\/", test["uri"])
            if match:
                log.error("This stream is encrypted. Use --hls option")
                sys.exit(2)
            manifest = "%s?hdcore=2.8.0&g=hejsan" % test["path"]
            download_hds(options, manifest, options.output, swf)

class Svtplay():
    def get(self, options, url):
        url = url + "?type=embed"
        data = get_http_data(url)
        match = re.search("value=\"(/(public)?(statiskt)?/swf/video/svtplayer-[0-9\.]+swf)\"", data)
        swf = "http://www.svtplay.se" + match.group(1)
        options.other = "-W " + swf
        url = url + "&output=json&format=json"
        data = json.loads(get_http_data(url))
        options.live = data["video"]["live"]
        streams = {}

        for i in data["video"]["videoReferences"]:
            if self.options.hls and i["playerType"] == "ios":
                stream = {}
                stream["url"] = i["url"]
                streams[int(i["bitrate"])] = stream
            elif not self.options.hls and i["playerType"] == "flash":
                stream = {}
                stream["url"] = i["url"]
                streams[int(i["bitrate"])] = stream

        if len(streams) == 0:
            log.error("Can't find any streams.")
            sys.exit(2)
        elif len(streams) == 1:
            test = streams[streams.keys()[0]]
        else:
            test = select_quality(options, streams)

        if test["url"][0:4] == "rtmp":
            download_rtmp(options, test["url"], options.output, options.live, options.other, options.resume)
        elif self.options.hls:
            download_hls(options, test["url"], options.output, options.live, options.other)
        elif test["url"][len(test["url"])-3:len(test["url"])] == "f4m":
            match = re.search("\/se\/secure\/", test["url"])
            if match:
                log.error("This stream is encrypted. Use --hls option")
                sys.exit(2)
            manifest = "%s?hdcore=2.8.0&g=hejsan" % test["url"]
            download_hds(options, manifest, options.output, swf)
        else:
            download_http(test["url"], options.output)
