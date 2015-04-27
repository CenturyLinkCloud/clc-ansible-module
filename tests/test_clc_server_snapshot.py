#!/usr/bin/python

import clc_server_snapshot as clc_server_snapshot
from clc_server_snapshot import ClcSnapshot
import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch
from mock import create_autospec
import unittest

class TestClcServerSnapshotFunctions(unittest.TestCase):


    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        reload(clc_server_snapshot)


    @patch.object(ClcSnapshot, 'clc')
    def test_set_clc_creds_w_token(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken'}):
            under_test = ClcSnapshot(self.module)
            under_test._set_clc_creds_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcSnapshot, 'clc')
    def test_set_clc_credentials_w_creds(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'dummyuser', 'CLC_V2_API_PASSWD': 'dummypwd'}):
            under_test = ClcSnapshot(self.module)
            under_test._set_clc_creds_from_env()
            mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='dummyuser', api_passwd='dummypwd')


    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcSnapshot(self.module)
            under_test._set_clc_creds_from_env()
        self.assertEqual(self.module.fail_json.called, True)


    def test_define_argument_spec(self):
        result = ClcSnapshot.define_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(ClcSnapshot, 'clc')
    def test_get_servers_from_clc_api(self, mock_clc_sdk):
        mock_clc_sdk.v2.Servers.side_effect = CLCException("Server Not Found")
        under_test = ClcSnapshot(self.module)
        under_test._get_servers_from_clc(['TESTSVR1', 'TESTSVR2'], 'FAILED TO OBTAIN LIST')
        self.module.fail_json.assert_called_once_with(msg='FAILED TO OBTAIN LIST: Server Not Found')


if __name__ == '__main__':
    unittest.main()
