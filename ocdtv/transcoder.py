# -*- coding: utf-8 -*-
#
# © 2010 Buster Marx, Inc. All rights reserved.
# Author: Ian Eure <ian.eure@gmail.com>
#

"""Transcode files."""

import os
import shutil
import time
import logging
import tempfile
from subprocess import check_call
from itertools import imap
from functools import partial
from operator import itemgetter

from ocdtv.filescanner import is_importable


def transcode_file(handbrake, preset, no_act, renamer, file_, metadata):
    """Transcode a file, returning its output path."""
    metadata['m4v_filename'] = os.path.splitext(file_)[0] + ".m4v"
    metadata['m4v_basename'] = os.path.basename(metadata['m4v_filename'])
    metadata['filename'] = file_

    output = renamer(metadata)
    spool = tempfile.mkstemp(suffix=".m4v")[1]
    args = (handbrake, "-Z", preset, "-i", file_, "-o", spool)
    logging.debug("Executing: %s", args)

    if no_act:
        print "Skipping transcode of %s to %s" % (file_, output)
        return output


    st = time.time()
    try:
        check_call(args)
    except BaseException, ex:
        # If transcoding failed, nuke the temp output file.
        try:
            os.unlink(spool)
        except:
            pass
        raise ex
    shutil.move(spool, output)
    logging.debug("Transcoded %s in %ds" % (os.path.basename(file_),
                                            time.time() - st))
    return output


def _compare(file_a, file_b):
    """Compare two files.

    If the filenames are the same, _always_ return a .m4v first, otherwise
    use a normal comparison."""
    (fe_a, fe_b) = imap(os.path.splitext,
                        imap(os.path.basename, (file_a, file_b)))

    return (-1 if fe_a[0] == fe_b[0] and fe_a[1].lower() == ".m4v"
            else 1 if fe_a[0] == fe_b[0] and fe_b[1].lower() == ".m4v"
            else cmp(file_a, file_b))


def transcoded(handbrake, preset, no_act, renamer, file_info):
    """Yield files which have been transcoded (if necessary)."""
    transcode = partial(transcode_file, handbrake, preset, no_act, renamer)
    good_files = []
    for (filename, metadata) in sorted(
        file_info, cmp=_compare, key=itemgetter(0)):
        base = os.path.splitext(os.path.basename(filename))[0]

        if base in good_files:
            continue

        if not is_importable(filename):
            filename = transcode(filename, metadata)

        good_files.append(base)
        yield (filename, metadata)
