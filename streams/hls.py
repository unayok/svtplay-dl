def parsem3u(data):
    if not data.startswith("#EXTM3U"):
        raise ValueError("Does not apprear to be a ext m3u file")

    files = []
    streaminfo = {}
    globdata = {}

    data = data.replace("\r","\n")
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


def download_hls(options, url, output, live, other):
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
        match = re.search("URI=\"(http://.*)\"", keydata)
        key = get_http_data(match.group(1))
        rand = os.urandom(16)
    except:
        pass

    try:
        from Crypto.Cipher import AES
        decryptor = AES.new(key, AES.MODE_CBC, rand)
    except ImportError:
        log.error("You need to install pycrypto to download encrypted HLS streams")
        sys.exit(2)
    n = 1
    if output != "-":
        extension = re.search("(\.[a-z0-9]+)$", output)
        if not extension:
            output = output + ".ts"
        log.info("Outfile: %s", output)
        file_d = open(output, "wb")
    else:
        file_d = sys.stdout

    for i in files:
        if output != "-":
            progressbar(len(files), n)
        data = get_http_data(i[0])
        if encrypted:
            lots = StringIO.StringIO(data)

            plain = ""
            crypt = lots.read(1024)
            decrypted = decryptor.decrypt(crypt)
            while decrypted:
                plain += decrypted
                crypt = lots.read(1024)
                decrypted = decryptor.decrypt(crypt)
            data = plain

        file_d.write(data)
        n += 1

    if output != "-":
        file_d.close()
        progress_stream.write('\n')