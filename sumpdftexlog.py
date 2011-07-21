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
import os

terminal_width,_ = console.getTerminalSize()

# argument parsing definitions

parser = argparse.ArgumentParser(prog='sumpdftexlog',
                                 description='Summarize log of pdfTex')
parser.add_argument('input',
                    metavar='INPUT',
                    help='pdfLaTeX log file',
                    nargs=1,
                    type=argparse.FileType('r'))
parser.add_argument('-g', '--graphics',
                    action='store_true',
                    dest='graphics',
                    help='Write out graphics files')
parser.add_argument('-f', '--local',
                    action='store_true',
                    dest='local',
                    help='Write out local files')
parser.add_argument('-w', '--warnings',
                    action='store_true',
                    dest='warnings',
                    help='Write out warnings')
parser.add_argument('-V', '--verbose',
                    action='store_true',
                    dest='verbose',
                    help='Be verbose')
parser.add_argument('-v', '--version',
                    action='version',
                    version='%(prog)s ' + version)
args = parser.parse_args()

# open log file for parsing
log = open(args.input[0].name)

log_data = log.readlines()
# make one big long string
log_data = str.join('',log_data)

total = {}
total['Info'] = len(re.findall('Info:',log_data))
total['Warning'] = len(re.findall(str.join('[\n]?',[' ','[Ww]','a','r','n','i','n','g','[: ]']),log_data))
total['Error'] = len(re.findall('\n!',log_data))

# change all () that don't begin with a filename to <>
# this re only works for unix filesystems currently
regex = '\((?![\./])[^()]*\)'
def replace_all_match_tips(regex,string,left='<',right='>'):
    regex = re.compile(regex)
    while regex.search(string):
        span = regex.search(string).span()
        start = span[0]
        end = span[1] - 1
        new = string[:start]
        new += left
        new += string[start+1:end]
        new += right
        new += string[end+1:]
        string = new
    return string
log_data = replace_all_match_tips(regex,log_data)

# parse by groups of \( \)
def get_groups(string, start='(', end=')'):
    start = re.escape(start)
    end = re.escape(end)
    try:
        initial = re.search(start,string).start()
    except AttributeError:
        return [string]
    level = 1
    groups = []
    groups.append(string[:initial])
    groups.append([])
    string = string[(initial+1):]
    current_group = groups[-1]
    #import pdb; pdb.set_trace()
    while len(string) > 0:
        left = re.search(start,string)
        right = re.search(end,string)
        if right:
            if left and left.start() < right.start():
                initial = left.start()
                level += 1
                if initial > 0:
                    current_group.append(string[:initial])
                current_group.append([])
                current_group = current_group[-1]
            else:
                level -= 1
                initial = right.start()
                if initial > 0:
                    current_group.append(string[:initial])
                current_group = groups
                for i in range(level):
                    current_group = current_group[-1]
            string = string[(initial+1):]
        else:
            groups.append(string)
            string = ''
    return groups

groups = get_groups(log_data)

def get_filename(string):
    newline_split = string.split('\n')
    option_one = newline_split[0]
    #TODO  shouldn't look for if file exists on os...should just parse
    try:
        option_two = option_one + newline_split[1].split(' \n')[0]
        if os.path.exists(option_two):
            return option_two
    except:
        pass
    if os.path.exists(option_one):
        return option_one
    else:
        return False

messages = {'Graphic':[],'Info':[],'Warning':[],'Error':[]}
#messages['Info'] = len(re.findall('Info:',log_data))

def strip_by_regex(regex,string):
    res = re.search(regex,string)
    if res:
        span = res.span()
        string = string[:span[0]]
        string += string[span[1]:]
        removed = string[span[0]:span[1]]
    else:
        removed = None
    return string,removed

def add_file(matchobj):
    string = matchobj.group(0)
    graph = re.search(' Graphic file \<',string).span()
    filename = string[6:graph[0]]
    messages['Graphic'].append(filename)

    return ''

global current_filename
global filenames
filenames = []
def add_error(matchobj):
    string = matchobj.group(0)
    split = string.split('\n')
    message = split[1][2:]
    span = re.search('\nl.[0-9]* ',string).span()
    line = int(string[span[0]+3:span[1]-1])
    command = string[span[1]:]
    command = command.split('\n')[0]
    new_error = {}
    new_error['line'] = line
    new_error['filename'] = current_filename
    new_error['message'] = message + ': ' + command
    messages['Error'].append(new_error)
    return ''

def add_undefined_ref(matchobj):
    string = matchobj.group(0)
    split = string.split(' ')
    ref = split[3]
    page = int(split[6])
    line = int(split[-1][:-1])
    new_warn = {}
    new_warn['line'] = line
    new_warn['message'] = ref + ' is undefined'
    new_warn['page'] = page
    new_warn['filename'] = current_filename
    new_warn['package'] = 'LaTeX'
    messages['Warning'].append(new_warn)
    return ''
    
def add_pdfTeX_warning(matchobj):
    string = matchobj.group(0)
    string = string[re.search(': ',string).span()[1]:]
    line = int(string[re.search('\nl\.[0-9]*',string).span()[0]+3:])
    message = re.sub('\n','',string[:40])
    split = string.split(' ')
    new_warn = {}
    new_warn['line'] = line
    new_warn['message'] = message
    new_warn['filename'] = current_filename
    new_warn['package'] = 'pdfTeX'
    messages['Warning'].append(new_warn)
    return ''

def add_generic_package_warning(matchobj):
    string = matchobj.group(0)
    warning = re.search(' Warning',string).span()
    package = string[9:warning[0]]
    split = string.split(' ')
    line = int(split[-1][:-1])
    new_warn = {}
    new_warn['line'] = line
    new_warn['message'] = ''
    new_warn['filename'] = current_filename
    new_warn['package'] = package
    messages['Warning'].append(new_warn)
    return ''

def add_generic_class_warning(matchobj):
    string = matchobj.group(0)
    warning = re.search(' Warning: ',string).span()
    package = string[7:warning[0]]
    split = string.split(' ')
    message = string[warning[1]:-1]
    new_warn = {}
    new_warn['line'] = None
    new_warn['message'] = message
    new_warn['filename'] = current_filename
    new_warn['package'] = package
    messages['Warning'].append(new_warn)
    return ''

def add_version_warning(matchobj):
    string = matchobj.group(0)
    package = re.search('document class .*?,\n',string).span()
    package = string[package[0]+15:package[1]-2]
    new_warn = {}
    new_warn['line'] = None
    new_warn['message'] = 'Requested ' + package + ' version unavailable.'
    new_warn['filename'] = current_filename
    new_warn['package'] = 'LaTeX'
    messages['Warning'].append(new_warn)
    return ''

def add_multiple_label(matchobj):
    string = matchobj.group(0)
    split = string.split(' ')
    message = str.join(' ',split[2:])
    new_warn = {}
    new_warn['line'] = None
    new_warn['message'] = message
    new_warn['filename'] = current_filename
    new_warn['package'] = 'LaTeX'
    messages['Warning'].append(new_warn)
    return ''

def get_messages(group):
    global current_filename
    #import pdb; pdb.set_trace()
    for i in range(len(group)):
        if type(group[i]) is str:
            if i == 0 and get_filename(group[i]):
                filename = get_filename(group[i])
                filenames.append(filename)
            # parse for messages
            try:
                current_filename = filename
            except:
                pass
            string = group[i]
            regex = '\n!(.|\n)*?\nl.[0-9]* .*?\n'
            string = re.sub(regex,add_error,string)
            # pdfTeX warnings
            regex = str.join('\n?',list('pdfTeX warning '))
            regex += '(.|\n)*?\nl\.[0-9]*'
            string = re.sub(regex,add_pdfTeX_warning,string)
            # generic package warning
            regex = '\nPackage .*? Warning: .*? on input line [0-9]*\.'
            string = re.sub(regex,add_generic_package_warning,string)
            # generic class warning
            regex = '\nClass .*? Warning: .*\n'
            string = re.sub(regex,add_generic_class_warning,string)
            # LaTeX version warning
            regex = '\nLaTeX Warning: You have requested, on input line [0-9]*, version\n(.|\n)*?is available.\n'
            string = re.sub(regex,add_version_warning,string)
            #import pdb; pdb.set_trace()
            # the remaining need the string stripped
            string = re.sub('\n','',string)
            # graphic files
            regex = 'File: .*? Graphic file \<type [a-zA-Z0-9]*\>'
            string = re.sub(regex,add_file,string)
            # undefined reference
            regex = 'LaTeX Warning: Reference .*? on page [0-9]* undefined on input line [0-9]*\.'
            string = re.sub(regex,add_undefined_ref,string)
            # multiply defined labels
            regex = 'LaTeX Warning: Label `.*?\' multiply defined\.'
            string = re.sub(regex,add_multiple_label,string)
            # 'There were undefined references'
            regex = 'LaTeX Warning: There were undefined references.'
            regex = re.compile(regex)
            if regex.search(string):
                string = regex.sub('',string)
                messages['Warning'].append({'line':None,
                                            'package':'LaTeX',
                                            'message':'There were undefined references',
                                            'filename':current_filename})
            # 'There were multiply-defind labels'
            regex = 'LaTeX Warning: There were multiply-defined labels.'
            regex = re.compile(regex)
            if regex.search(string):
                string = regex.sub('',string)
                messages['Warning'].append({'line':None,
                                            'package':'LaTeX',
                                            'message':'There were multiply-defined labels',
                                            'filename':current_filename})

        else:
            get_messages(group[i])

get_messages(groups)

#print(repr(messages))

head_fmt = '{:<12s}{:5d} messages found\n'
line_fmt = '{:>12s} {:s}\n'

unique_filenames = []
for i in filenames:
    if i not in unique_filenames:
        unique_filenames.append(i)
local_filenames = []
for i in filenames:
    if i[0] == '.' and i not in local_filenames:
        local_filenames.append(i)


# files
print('{:10s} {:5d} of {:5d} parsed files are local'.format('Files:',len(local_filenames),len(filenames)))
if args.local:
    for i in local_filenames:
        print(i)
# graphics
print('{:10s} {:5d} files used as graphics'.format('Graphics:',len(messages['Graphic'])))
if args.graphics:
    for i in messages['Graphic']:
        print('    {:s}'.format(i))

print('{:10s} {:5d} of {:5d} parsed'.format('Info:',len(messages['Info']),total['Info']))

#warnings
print('{:10s} {:5d} of {:5d} parsed'.format('Warnings:',len(messages['Warning']),total['Warning']))
if args.warnings:
    for i in messages['Warning']:
        if i['line'] is None:
            line = 0
        else:
            line = i['line']
        print('{:6d}:{:23s}{:10s}{:s}'.format(line,
                                              i['filename'],
                                              i['package'],
                                              i['message']))

#errors
print('Errors found: {:5d}'.format(len(messages['Error'])))
for i in messages['Error']:
    print('{:6d}:{:23s}{:s}'.format(i['line'],
                                    i['filename'],
                                    i['message']))


if args.verbose:
    print('I was being verbose.')
