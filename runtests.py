#!/usr/bin/env python

import os
os.chdir('test')

import sys, subprocess

errno = subprocess.call([sys.executable, 'test_tags2set.py'])
if errno:
    raise SystemExit(errno)

