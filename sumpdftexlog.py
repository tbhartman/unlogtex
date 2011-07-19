#!/usr/bin/python3 -i

# Copyright 2011 Tim Hartman <tbhartman@gmail.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

version='alpha'

import argparse
import re
from collections import *
import datetime
import sys
import tempfile
import console

terminal_width,_ = console.getTerminalSize()

# argument parsing definitions

parser = argparse.ArgumentParser(prog='sumpdftexlog',
                                 description='Summarize log of pdfTex')
parser.add_argument('input',
                    metavar='INPUT',
                    help='Abaqus keyword file (limit one)',
                    nargs=1,
                    type=argparse.FileType('r'))
parser.add_argument('-V', '--verbose',
                    action='store_true',
                    dest='verbose',
                    help='Be verbose')
parser.add_argument('-v', '--version',
                    action='version',
                    version='%(prog)s ' + version)
args = parser.parse_args()


if args.verbose:
    print('I was being verbose.')
