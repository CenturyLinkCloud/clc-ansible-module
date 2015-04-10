#!/usr/bin/python

import clc_inv as clc_inv
from clc_inv import clcInventory
import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch
from mock import create_autospec
import unittest

class TestClcInvFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter=mock.MagicMock()


if __name__ == '__main__':
    unittest.main()
