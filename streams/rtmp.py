import re
import subprocess
import logging
import shlex

log = logging.getLogger('svtplay_dl')

def download_rtmp(options, url, output, live, extra_args, resume):
    """ Get the stream from RTMP """
    args = []
    if live:
        args.append("-v")

    if resume:
        args.append("-e")

    extension = re.search("(\.[a-z0-9]+)$", url)
    if output != "-":
        if not extension:
            extension = re.search("-y (.+):[-_a-z0-9\/]", extra_args)
            if not extension:
                output = output + ".flv"
            else:
                output = output + "." + extension.group(1)
        else:
            output = output + extension.group(1)
        log.info("Outfile: %s", output)
        args += ["-o", output]
    if options.silent or output == "-":
        args.append("-q")
    if extra_args:
        args += shlex.split(extra_args)
    command = ["rtmpdump", "-r", url] + args
    try:
        subprocess.call(command)
    except OSError as e:
        log.error("Could not execute rtmpdump: " + e.strerror)