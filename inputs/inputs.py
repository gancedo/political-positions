from __future__ import division
import csv
from percept.conf.base import settings
from percept.utils.input import DataFormats
from percept.tests.framework import CSVInputTester
from percept.datahandlers.inputs import BaseInput
from percept.utils.models import get_namespace
import os
from itertools import chain
import logging
import json
import re
import pandas as pd
import subprocess
from pandas.io import sql
import sqlite3
import json
import requests
import subprocess

log = logging.getLogger(__name__)

def join_path(p1,p2):
    return os.path.abspath(os.path.join(p1,p2))

class SenateFormats(DataFormats):
    sjson = "sjson"

class SenateInput(BaseInput):
    """
    Extends baseinput to read simpsons scripts
    """
    input_format = SenateFormats.mjson
    help_text = "Read in music links data."
    namespace = get_namespace(__module__)

    def read_input(self, mfile, has_header=True):
        """
        directory is a path to a directory with multiple csv files
        """

        mjson= json.load(open(mfile))
        for m in mjson:
            m['ltype'] = m['ltype'].split("?")[0]
        ltypes = list(set([m['ltype'] for m in mjson]))
        for l in ltypes:
            jp = join_path(settings.MUSIC_PATH,l)
            if not os.path.isdir(jp):
                os.mkdir(jp)

        fpaths = []
        for m in mjson:
            fname = m['link'].split("/")[-1]
            fpath = join_path(join_path(settings.MUSIC_PATH,m['ltype']),fname)
            try:
                if not os.path.isfile(fpath):
                    r = requests.get(m['link'])
                    f = open(fpath, 'wb')
                    f.write(r.content)
                    f.close()
                fpaths.append({'type' : m['ltype'], 'path' : fpath})
            except Exception:
                log.exception("Could not get music file.")

        for p in fpaths:
            newfile = p['path'][:-4] + ".ogg"
            if not os.path.isfile(newfile):
                frommp3 = subprocess.Popen(['mpg123', '-w', '-', p['path']], stdout=subprocess.PIPE)
                toogg = subprocess.Popen(['oggenc', '-'], stdin=frommp3.stdout, stdout=subprocess.PIPE)
                with open(newfile, 'wb') as outfile:
                    while True:
                        data = toogg.stdout.read(1024 * 100)
                        if not data:
                            break
                        outfile.write(data)
            p['newpath'] = newfile

        self.data = fpaths