import sys
if sys.version_info > (3, 0):
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
    from urllib.parse import urlparse, parse_qs, unquote_plus, quote_plus
else:
    from urllib2 import Request, urlopen, HTTPError, URLError
    from urlparse import urlparse, parse_qs
    from urllib import unquote_plus, quote_plus

import os

progress_stream = sys.stderr

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
        log.error("Something wrong with that url")
        log.error("Error code: %s" % e.code)
        sys.exit(5)
    except URLError as e:
        log.error("Something wrong with that url")
        log.error("Error code: %s" % e.reason)
        sys.exit(5)
    except ValueError as e:
        log.error("Try adding http:// before the url")
        sys.exit(5)
    if sys.version_info > (3, 0):
        data = response.read().decode('utf-8')
    else:
        try:
            data = response.read()
        except socket.error as e:
            log.error("Lost the connection to the server")
            sys.exit(5)
    response.close()
    return data

def progress(byte, total):
    """ Print some info about how much we have downloaded """
    ratio = float(byte) / total
    percent = round(ratio*100, 2)
    tlen = str(len(str(total)))
    fmt = "Downloaded %"+tlen+"dkB of %dkB bytes (% 3.2f%%)"
    progresstr = fmt % (byte >> 10, total >> 10, percent)

    columns = int(os.getenv("COLUMNS", "80"))
    if len(progresstr) < columns - 13:
        p = int((columns - len(progresstr) - 3) * ratio)
        q = int((columns - len(progresstr) - 3) * (1 - ratio))
        progresstr = "[" + ("#" * p) + (" " * q) + "] " + progresstr
    progress_stream.write(progresstr + '\r')

    if byte >= total:
        progress_stream.write('\n')

    progress_stream.flush()

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

def progressbar(total, pos, msg=""):
    """
    Given a total and a progress position, output a progress bar
    to stderr. It is important to not output anything else while
    using this, as it relies soley on the behavior of carriage
    return (\\r).

    Can also take an optioal message to add after the
    progressbar. It must not contain newliens.

    The progress bar will look something like this:

    [099/500][=========...............................] ETA: 13:36:59

    Of course, the ETA part should be supplied be the calling
    function.
    """
    width = 50 # TODO hardcoded progressbar width
    rel_pos = int(float(pos)/total*width)
    bar = str()

    # FIXME ugly generation of bar
    for i in range(0, rel_pos):
        bar += "="
    for i in range(rel_pos, width):
        bar += "."

    # Determine how many digits in total (base 10)
    digits_total = len(str(total))
    fmt_width = "%0" + str(digits_total) + "d"
    fmt = "\r[" + fmt_width + "/" + fmt_width + "][%s] %s"

    progress_stream.write(fmt % (pos, total, bar, msg))