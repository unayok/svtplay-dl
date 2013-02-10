#!/usr/bin/python
import handlers
import sys
import logging

log = logging.getLogger('svtplay_dl')

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

setup_log(False)
handlers.handle(sys.argv[1])
