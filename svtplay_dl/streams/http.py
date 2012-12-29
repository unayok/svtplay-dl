from __future__ import absolute_import

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
import logging
import time
from ..utils import *

log = logging.getLogger('svtplay_dl')

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
        file_d = open(options.output,"wb")
    else:
        file_d = sys.stdout

    lastprogress = 0
    while 1:
        chunk = response.read(8192)
        bytes_so_far += len(chunk)

        if not chunk:
            break

        file_d.write(chunk)
        if output != "-":
            now = time.time()
            if lastprogress + 1 < now:
                lastprogress = now
                progress(bytes_so_far, total_size)

    if options.output != "-":
        file_d.close()