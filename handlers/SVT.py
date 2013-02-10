#!/usr/bin/env python

import logging
log = logging.getLogger('svtplay_dl')

def handle_url(url) :
    if 'svtplay.se' in url :
        log.info("SVTplay URL detected")
        return True
    return False



