#!/usr/bin/python3

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

log = open(args.input[0].name)

class Group(list):
    write_out = False

    def __init__(self, write_out):
        self.write_out = write_out

messages = {'Info':Group(False),
            'Warning':Group(True),
            'Error':Group(True)}

error_re = re.compile('^\!')
line_re = re.compile('^l.[0-9]')

current = None
for line in log.readlines():
    if error_re.search(line):
        current = {}
        current['message'] = line[2:].strip()
        messages['Error'].append(current)
    if line_re.search(line) and 'line' not in current:
        split = line.split(' ')
        current['line'] = int(split[0][2:])

head_fmt = '{:<12s}{:5d} messages found\n'
line_fmt = '{:>12s} {:s}\n'
for i in messages:
    print(head_fmt.format(i,len(messages[i])), end='')
    if messages[i].write_out:
        for j in messages[i]:
            print(line_fmt.format(('[' + str(j['line']) + ']'), j['message']),end='')


if args.verbose:
    print('I was being verbose.')
