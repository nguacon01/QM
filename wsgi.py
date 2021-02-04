from app.Jobs import DONE_JOBS
from flask import Flask, redirect, url_for, request, render_template
import time
from datetime import datetime, timedelta
from xml.sax import handler, make_parser
import glob
import os
import os.path as op
import sys
import json
try:
    from uptime import uptime # installed uptime module at Pasteur
except:
    print ("no uptime module")
from subprocess import check_output

from configparser import ConfigParser

import app as queueManager

app = Flask(__name__)

#!/usr/bin/env python
# encoding: utf-8
"""
# mini WEB server for QueueManager

# see http://bottle.paws.de/docs/dev/index.html

# Created by Marc-Andre on 2015-4-14 based on an early version 2011-01-26.

# This code is Licenced under the Cecill licence code

# """

@app.route('/')
@app.route('/index')
def index():
    queue = queueManager.get_QM()
    return queue


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, debug=True)