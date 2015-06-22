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

    @patch.object(ClcAlertPolicy, '_get_alert_policies')
    @patch.object(ClcAlertPolicy, '_ensure_alert_policy_is_present')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_process_request_state_present(self, mock_set_clc_creds, mock_ensure_alert_policy, mock_get_alert_policies):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'cpu'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'present'
        }
        mock_ensure_alert_policy.return_value = True, 'success'
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcAlertPolicy(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, policy='success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_get_alert_policies')
    @patch.object(ClcAlertPolicy, '_ensure_alert_policy_is_absent')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_process_request_state_absent(self, mock_set_clc_creds, mock_ensure_alert_policy, mock_get_alert_policies):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'cpu'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'absent'
        }
        mock_ensure_alert_policy.return_value = True, None
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcAlertPolicy(self.module)
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, policy=None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_create_alert_policy')
    @patch.object(ClcAlertPolicy, '_alert_policy_exists')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_present_new(self, mock_set_clc_creds, mock_alert_policy_exists, mock_create):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'cpu'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'absent'
        }
        mock_alert_policy_exists.return_value = False
        mock_create.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcAlertPolicy(self.module)
        changed, policy = under_test._ensure_alert_policy_is_present()
        self.assertEqual(changed, True)
        self.assertEqual(policy,'success')

    @patch.object(ClcAlertPolicy, '_create_alert_policy')
    @patch.object(ClcAlertPolicy, '_alert_policy_exists')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_present_no_name(self, mock_set_clc_creds, mock_alert_policy_exists, mock_create):
        test_params = {
            'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'cpu'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'absent'
        }
        mock_alert_policy_exists.return_value = False
        mock_create.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcAlertPolicy(self.module)
        under_test._ensure_alert_policy_is_present()
        self.module.fail_json.assert_called_once_with(msg='Policy name is a required')

    @patch.object(ClcAlertPolicy, '_ensure_alert_policy_is_updated')
    @patch.object(ClcAlertPolicy, '_alert_policy_exists')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_present_existing(self, mock_set_clc_creds, mock_alert_policy_exists, mock_update):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'cpu'
            , 'duration': 'duration'
            , 'threshold': 'threashold'
            , 'state': 'absent'
        }
        mock_alert_policy_exists.return_value = mock.MagicMock()
        mock_update.return_value = True, 'success'
        self.module.params = test_params
        self.module.check_mode = False

        under_test = ClcAlertPolicy(self.module)
        changed, policy = under_test._ensure_alert_policy_is_present()
        self.assertEqual(changed, True)
        self.assertEqual(policy,'success')

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(ClcAlertPolicy, '_get_alert_policy_id')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_absent_name_only(self, mock_set_clc_creds, mock_get_id, mock_delete):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'state': 'absent'
        }
        mock_get_id.return_value = '12345'
        mock_delete.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345', '23456'}
        changed, policy = under_test._ensure_alert_policy_is_absent()
        self.assertEqual(changed, True)
        self.assertEqual(policy,None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(ClcAlertPolicy, '_get_alert_policy_id')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_absent_id_only(self, mock_set_clc_creds, mock_get_id, mock_delete):
        test_params = {
            'id': 'testid'
            , 'alias': 'testalias'
            , 'state': 'absent'
        }
        mock_get_id.return_value = '12345'
        mock_delete.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345', 'testid'}
        changed, policy = under_test._ensure_alert_policy_is_absent()
        self.assertEqual(changed, True)
        self.assertEqual(policy,None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(ClcAlertPolicy, '_get_alert_policy_id')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_absent_no_id_present(self, mock_set_clc_creds, mock_get_id, mock_delete):
        test_params = {
            'id': 'testid'
            , 'alias': 'testalias'
            , 'state': 'absent'
        }
        mock_get_id.return_value = '12345'
        mock_delete.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345', '23456'}
        changed, policy = under_test._ensure_alert_policy_is_absent()
        self.assertEqual(changed, False)
        self.assertEqual(policy,None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(ClcAlertPolicy, '_get_alert_policy_id')
    @patch.object(ClcAlertPolicy, '_set_clc_credentials_from_env')
    def test_ensure_alert_policy_is_absent_no_id_no_name(self, mock_set_clc_creds, mock_get_id, mock_delete):
        test_params = {
            'alias': 'testalias'
            , 'state': 'absent'
        }
        mock_get_id.return_value = '12345'
        mock_delete.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcAlertPolicy(self.module)
        under_test.policy_dict = {'12345', '23456'}
        changed, policy = under_test._ensure_alert_policy_is_absent()
        self.module.fail_json.assert_called_once_with(msg='Either alert policy id or policy name is required')


if __name__ == '__main__':
    unittest.main()
