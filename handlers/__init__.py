import handlers.SVT
import handlers.TV4

import logging
log = logging.getLogger('svtplay_dl')

handlers = {}
for x in globals().values() :
    if hasattr( x, 'handle_url' ) :
        handlers[x.__name__] = x.handle_url

def handle(url) :
    for name, handler in handlers.iteritems() :
        if handler(url) :
            log.info("handled by %s" % name)
            break
    else :
        log.error("unhandled URL: " + url)
