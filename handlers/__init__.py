import os
import os.path
import inspect
import sys
import importlib
import logging
log = logging.getLogger('svtplay_dl')

handlers = {}
#for x in globals().values() :
#    if hasattr( x, 'handle_url' ) :
#        handlers[x.__name__] = x.handle_url

def handle(url, options) :
    for name, handler in handlers.iteritems() :
        if handler(url, options) :
            log.info("handled by %s" % name)
            break
    else :
        log.error("unhandled URL: " + url)

def load_handlers(path = None):
    if not path :
        path = os.path.dirname(inspect.getfile(sys.modules[__name__]))
    pwd = os.getcwd() + "/"
    def look(module_name) :
        global handlers
        module = importlib.import_module(module_name)
        if hasattr( module, "handle_url" ) :
            print module_name
            handlers[module_name] = module.handle_url

    for root, dirs, files in os.walk(path) :
        for fname in files :
            if fname.endswith(".py") :
                path = os.path.join(root, fname).replace(pwd,"")
                mname = path.rsplit(".", 1)[0].replace("/",".").strip(".")
                look(mname)
