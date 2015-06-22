#!/usr/bin/python

import clc_ansible_module.clc_alert_policy as clc_alert_policy
from clc_ansible_module.clc_alert_policy import ClcAlertPolicy
import clc as clc_sdk
import mock
from mock import patch, create_autospec
import os
import unittest

# This is a pretty brute-force attack at unit testing.
# This is my first stab, so anyone reading this who is more Python-inclined
# is both welcome and encouraged to make it better.

        # self.clc.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')
def FakeAnsibleModule():
    module = mock.MagicMock()
    module.check_mode = False
    module.params = {}
    return module

class TestClcAlertPolicy(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = FakeAnsibleModule()
        self.policy = ClcAlertPolicy(self.module)
        self.policy.module.exit_json = mock.MagicMock()



    def notestNoCreds(self):
        self.policy.module.fail_json = mock.MagicMock(side_effect=Exception('nocreds'))
        try:
            result = self.policy.do_work()
        except:
            pass
        self.assertEqual(self.policy.module.fail_json.called, True)

    def testLoginMagic(self):
        self.policy.clc.v2.SetCredentials = mock.MagicMock()
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME':'passWORD', 'CLC_V2_API_PASSWD':'UsErnaME'}):
            try:
                self.policy.process_request()
            except:
                # It'll die, and we don't care
                pass

        self.policy.clc.v2.SetCredentials.assert_called_once_with(api_username='passWORD',api_passwd='UsErnaME')

    @patch.object(ClcAlertPolicy, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            under_test = ClcAlertPolicy(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcAlertPolicy, 'clc')
    def test_set_clc_credentials_w_creds(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'dummyuser', 'CLC_V2_API_PASSWD': 'dummypwd'}):
            under_test = ClcAlertPolicy(self.module)
            under_test._set_clc_credentials_from_env()
            mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='dummyuser', api_passwd='dummypwd')

    @patch.object(ClcAlertPolicy, 'clc')
    def test_set_clc_credentials_w_api_url(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_URL': 'dummyapiurl'}):
            under_test = ClcAlertPolicy(self.module)
            under_test._set_clc_credentials_from_env()
            self.assertEqual(under_test.clc.defaults.ENDPOINT_URL_V2, 'dummyapiurl')

    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcAlertPolicy(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(self.module.fail_json.called, True)

    @patch.object(clc_alert_policy, 'AnsibleModule')
    @patch.object(clc_alert_policy, 'ClcAlertPolicy')
    def test_main(self, mock_ClcAlertPolicy, mock_AnsibleModule):
        mock_ClcAlertPolicy_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcAlertPolicy.return_value   = mock_ClcAlertPolicy_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_alert_policy.main()

        mock_ClcAlertPolicy.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcAlertPolicy_instance.process_request.assert_called_once()


if __name__ == '__main__':
    unittest.main()
