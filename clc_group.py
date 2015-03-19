#!/usr/bin/python

import sys
import os
import datetime
import json
from ansible.module_utils.basic import *

#
#  Requires the clc-python-sdk.
#  sudo pip install clc-sdk
#
try:
    import clc as clc_sdk
except ImportError:
    clc_found = False
    clc_sdk = None
else:
    clc_found = True