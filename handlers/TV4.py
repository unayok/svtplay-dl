#!/usr/bin/env python

import logging
log = logging.getLogger('svtplay_dl')

def handle_url(url) :
    if 'tv4play.se' in url :
        log.info("TV4play URL detected")
        return True
    return False
