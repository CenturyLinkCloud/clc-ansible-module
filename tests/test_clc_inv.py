#!/usr/bin/python

import clc_inv as clc_inv
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

    @patch('clc_inv.clc')
    def test_find_hostvars_for_single_server(self, mock_clc_sdk):
        server = mock.MagicMock()
        server.name = 'testServerWithNoDetails'
        server.data = {}
        mock_clc_sdk.v2.Server.return_value = server
        result = clc_inv._find_hostvars_for_single_server('testServerWithNoDetails')
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
