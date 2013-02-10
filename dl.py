#!/usr/bin/python
import handlers
import sys
import logging
from optparse import OptionParser
from handlers.util import get_http_data
import re

log = logging.getLogger('svtplay_dl')
progress_stream = sys.stderr

__version__ = "0.8.2013.01.26"

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
        self.progress = self._progress
        self.progressbar = self._progressbar

    def _progress(self, byte, total, extra = "") :
        progress(byte, total, extra)

    def _progressbar(self, total, pos, msg = "" ) :
        progressbar(total, pos, msg)

def progress(byte, total, extra = ""):
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
    progress_stream.write(progresstr + ' ' + extra + '\r')

    if byte >= total:
        progress_stream.write('\n')

    progress_stream.flush()

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

def get_media(url, options):
    if not options.output or os.path.isdir(options.output):
        data = get_http_data(url)
        match = re.search("(?i)<title.*>\s*(.*?)\s*</title>", data)
        if match:
            if sys.version_info > (3, 0):
                title = re.sub('[^\w\s-]', '', match.group(1)).strip().lower()
                if options.output:
                    options.output = options.output + re.sub('[-\s]+', '-', title)
                else:
                    options.output = re.sub('[-\s]+', '-', title)
            else:
                title = unicode(re.sub('[^\w\s-]', '', match.group(1)).strip().lower())
                if options.output:
                    options.output = unicode(options.output + re.sub('[-\s]+', '-', title))
                else:
                    options.output = unicode(re.sub('[-\s]+', '-', title))

    handlers.load_handlers()
    if not handlers.handle(url, options) :
        log.error("That site is not supported. Make a ticket or send a message.")
        sys.exit(2)

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
    options.progress = lambda *a : progress( *a )
    options.progressbar = lambda *a : progressbar( *a )
    if len(args) != 1:
        parser.error("incorrect number of arguments")

    setup_log(options.silent)

    url = args[0]
    get_media(url, options)
    progress_stream.write('\n')
    progress_stream.flush()

if __name__ == "__main__":
    main()
