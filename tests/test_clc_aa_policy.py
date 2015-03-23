#!/usr/bin/python

import clc_aa_policy as ClcAntiAffinityPolicy
import clc as clc_sdk
import mock
from mock import patch, create_autospec
import os
import unittest

class TestClcAntiAffinityPolicyFunctions(unittest.TestCase):

    #@patch.object(ClcAntiAffinityPolicy, '__init__')
    def setUp(self):
        self.obj = ClcAntiAffinityPolicy()
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()


    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            self.obj._clc_set_credentials(self.clc)

        self.clc.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')


    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            clc_aa_policy.obj._clc_set_credentials(self.clc)
            self.assertEqual(self.module.fail_json.called, True)




if __name__ == '__main__':
    unittest.main()