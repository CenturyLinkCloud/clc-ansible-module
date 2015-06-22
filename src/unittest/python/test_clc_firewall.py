__author__ = 'jonathanhinds'



import clc_ansible_module.clc_firewall as clc_firewall
from clc_ansible_module.clc_firewall import ClcFirewall

import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch
from mock import create_autospec
import unittest

class TestClcFirewall(unittest.TestCase):
    pass