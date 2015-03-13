#!/usr/bin/python

import datetime
import json
import clc

def main():
    date = str(datetime.datetime.now())
    print json.dumps({
        "time" : date
    })
    
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'absent']),
        )
    )

from ansible.module_utils.basic import *
main()