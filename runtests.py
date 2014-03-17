#!/usr/bin/env python

import os
import sys, subprocess

for test in '''
test/test_tags2set.py
test/test_uploadr.py
'''.split():
    errno = subprocess.call([sys.executable, test])
    if errno:
        raise SystemExit(errno)

