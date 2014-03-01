#!/usr/bin/env python

import os
import sys, subprocess

errno = subprocess.call([sys.executable, 'test/test_tags2set.py'])
if errno:
    raise SystemExit(errno)

