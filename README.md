# unlogtex

Summarize log of TeX

It undoes the mess of the log from TeX

## Introduction

Not much here yet, but this should eventually parse the log from Tex and output a summary of what happened.

Currently only pdfTeX output is supported.
There are several bugs I'm sure.
Oh, and not all warnings are parsed.  Yeah.

## Usage

usage: unlogtex [-h] [-g] [-f] [-w] [-V] [-v] INPUT

Summarize log of pdfTex

positional arguments:
  INPUT           pdfLaTeX log file

optional arguments:
  -h, --help      show this help message and exit
  -g, --graphics  Write out graphics files
  -f, --local     Write out local files
  -w, --warnings  Write out warnings
  -V, --verbose   Be verbose
  -v, --version   show program's version number and exit

## Bugs

View and report bugs at:
[bugs.teamhartman.org](http://bugs.teamhartman.org/project_page.php?project_id=7)

