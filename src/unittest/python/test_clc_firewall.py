#!/usr/bin/python



import clc_ansible_module.clc_firewall as clc_firewall
from clc_ansible_module.clc_firewall import ClcFirewall

import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch
from mock import create_autospec
import unittest

class TestClcFirewall(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter=mock.MagicMock()

    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(clc_firewall, 'clc_sdk') as mock_clc_sdk:
                under_test = ClcFirewall(self.module)
                under_test._set_clc_credentials_from_env()

        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(
            api_username='hansolo',
            api_passwd='falcon')

    def test_get_firewall_policy_fail(self):
        source_account_alias = 'WFAD'
        location = 'VA1'
        firewall_policy = 'fake_policy'


        mock_policy = mock.MagicMock()
        # mock_policy.return_value =
        test_firewall_policy = ClcFirewall(self.module)
        response, success = test_firewall_policy._get_firewall_policy(source_account_alias, location, firewall_policy)
        self.assertFalse(success)

    @patch.object(clc_firewall, 'clc_sdk')
    def test_get_firewall_policy_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        source_account_alias = 'WFAD'
        location = 'WA1'
        firewall_policy = 'test_policy'

        test_firewall = ClcFirewall(self.module)
        response, success = test_firewall._get_firewall_policy(source_account_alias, location, firewall_policy)
        self.assertTrue(success)
        self.assertEqual(response, mock_firewall_response)
        test_firewall.clc.v2.API.Call.assert_called_once_with('GET', '/v2-experimental/firewallPolicies/WFAD/WA1/test_policy')

    def test_get_firewall_policy_list_fail(self):
        source_account_alias = 'WFAD'
        location = 'VA1'

        mock_policy = mock.MagicMock()
        # mock_policy.return_value =
        test_firewall_policy = ClcFirewall(self.module)
        test_firewall_policy._get_firewall_policy_list(source_account_alias, location)
        self.assertTrue(self.module.fail_json.called)

    @patch.object(clc_firewall, 'clc_sdk')
    def test_get_firewall_policy_list_pass_w_destination_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        source_account_alias = 'WFAD'
        location = 'WA1'
        destination_account_alias = 'WAX'

        test_firewall = ClcFirewall(self.module)
        response = test_firewall._get_firewall_policy_list(source_account_alias, location, destination_account_alias)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, mock_firewall_response)
        test_firewall.clc.v2.API.Call.assert_called_once_with('GET', '/v2-experimental/firewallPolicies/WFAD/WA1?destinationAccount=WAX')

    @patch.object(clc_firewall, 'clc_sdk')
    def test_get_firewall_policy_list_pass_w_no_destination_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        source_account_alias = 'WFAD'
        location = 'WA1'

        test_firewall = ClcFirewall(self.module)
        response = test_firewall._get_firewall_policy_list(source_account_alias, location)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, mock_firewall_response)
        test_firewall.clc.v2.API.Call.assert_called_once_with('GET', '/v2-experimental/firewallPolicies/WFAD/WA1')

    def test_create_firewall_policy_fail(self):
        source_account_alias = 'WFAD'
        location = 'VA1'
        payload = {
            'destinationAccount': 'wfas',
            'source': '12345',
            'destination': '12345',
            'ports': 'any'
        }

        test_firewall_policy = ClcFirewall(self.module)
        test_firewall_policy._create_firewall_policy(source_account_alias, location, payload)
        self.assertTrue(self.module.fail_json.called)


    @patch.object(clc_firewall, 'clc_sdk')
    def test_create_firewall_policy_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        firewall_dict = {
            'source': '12345',
            'destination': '12345',
            'ports': 'any',
            'destination_account_alias': 'wfas'
        }

        test_firewall = ClcFirewall(self.module)
        response = test_firewall._create_firewall_policy(source_account_alias='WFAD', location='WA1', firewall_dict=firewall_dict)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, mock_firewall_response)
        test_firewall.clc.v2.API.Call.assert_called_once



    def test_delete_firewall_policy_fail(self):
        source_account_alias = 'WFAD'
        location = 'wa1'
        firewall_policy = 'this_is_not_a_real_policy'

        test_firewall_policy = ClcFirewall(self.module)
        test_firewall_policy._delete_firewall_policy(source_account_alias, location, firewall_policy)
        self.assertTrue(self.module.fail_json.called)

    @patch.object(clc_firewall, 'clc_sdk')
    def test_delete_firewall_policy_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        source_account_alias = 'WFAD'
        location = 'wa1'
        firewall_policy = 'this_is_not_a_real_policy'

        test_firewall = ClcFirewall(self.module)
        response = test_firewall._delete_firewall_policy(source_account_alias, location, firewall_policy)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, mock_firewall_response)
        test_firewall.clc.v2.API.Call.assert_called_once_with('DELETE', '/v2-experimental/firewallPolicies/%s/%s/%s' % (source_account_alias, location, firewall_policy))

    def test_ensure_firewall_policy_absent_fail(self):
        source_account_alias = 'WFAD'
        location = 'wa1'
        payload = {
            'destinationAccount': 'wfas',
            'source': '12345',
            'destination': '12345',
            'ports': 'any',
            'firewall_policy': 'this_is_not_a_real_policy'
        }
        test_firewall_policy = ClcFirewall(self.module)
        changed, policy, response =test_firewall_policy._ensure_firewall_policy_is_absent(source_account_alias, location, payload)
        self.assertFalse(changed)

    @patch.object(ClcFirewall, '_get_firewall_policy')
    @patch.object(ClcFirewall, '_delete_firewall_policy')
    def test_ensure_firewall_policy_absent_pass(self, mock_get_firewall_policy, mock_delete_firewall_policy):
        test = ClcFirewall(self.module)
        test._ensure_firewall_policy_is_absent()

    def test_ensure_firewall_policy_present_fail(self):
        source_account_alias = 'WFAD'
        location = 'wa1'
        payload = {
            'destinationAccount': 'wfas',
            'source': '12345',
            'destination': '12345',
            'ports': 'any',
            'firewall_policy': 'this_is_not_a_real_policy'
        }
        self.module.check_mode = False
        test_firewall_policy = ClcFirewall(self.module)
        changed, policy, response = test_firewall_policy._ensure_firewall_policy_is_present(source_account_alias, location, payload)
        self.assertTrue(self.module.fail_json.called)

    @mock.patch.object(ClcFirewall, '_create_firewall_policy')
    @mock.patch.object(ClcFirewall, '_get_policy_id_from_response')
    def test_ensure_firewall_policy_present_pass(self, mock_create_firewall_policy, mock_get_policy_id_from_response):
        source_account_alias = 'WFAD'
        location = 'VA1'
        firewall_dict = {'firewall_policy': 'something'}

        mock_firewall_response =[{'name': 'test', 'id': 'test'}]
        mock_get_policy_id_from_response.return_value = 'fake_policy'
        mock_create_firewall_policy.return_value = mock_firewall_response

        self.module.check_mode = False
        test_firewall = ClcFirewall(self.module)

        changed, policy_id, response = test_firewall._ensure_firewall_policy_is_present(source_account_alias, location, firewall_dict)

        self.assertFalse(self.module.fail_json.called)
        self.assertTrue(changed)
        self.assertEqual(policy_id, 'fake_policy')
        mock_create_firewall_policy.assert_called_once_with(source_account_alias, location, firewall_dict)
        mock_get_policy_id_from_response.assert_called_once_with(mock_firewall_response)

    @patch.object(clc_firewall, 'clc_sdk')
    def test_update_firewall_policy_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        source_account_alias = 'WFAD'
        location = 'WA1'
        test_firewall_policy = 'test_firewall_policy'
        firewall_dict = {
            'source': '12345',
            'destination': '12345',
            'ports': 'any',
            'destination_account_alias': 'wfas',
            'firewall_policy': test_firewall_policy
        }
        self.module.check_mode = False
        test_firewall = ClcFirewall(self.module)
        changed, policy_id, response = test_firewall._ensure_firewall_policy_is_present(source_account_alias, location, firewall_dict)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, mock_firewall_response)
        test_firewall.clc.v2.API.Call.assert_called_once_with('PUT', '/v2-experimental/firewallPolicies/%s/%s/%s' % (source_account_alias, location, test_firewall_policy), firewall_dict)

    def test_get_policy_id_from_response(self):
        test_policy_id = 'test_policy_id'
        test_response = {
            "links": [
                {
                    "rel": "self",
                    "href": "http://api.ctl.io/v2-experimental/firewallPolicies/wfad/va1/" + test_policy_id,
                    "verbs": [
                        "GET",
                        "PUT",
                        "DELETE"
                    ]
                }
            ]
        }
        test_firewall = ClcFirewall(self.module)
        policy_id = test_firewall._get_policy_id_from_response(test_response)
        self.assertEqual(policy_id, test_policy_id)


    def test_define_argument_spec(self):
        result = ClcFirewall._define_module_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(ClcFirewall, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            under_test = ClcFirewall(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcFirewall, 'clc')
    def test_set_clc_credentials_w_api_url(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_URL': 'dummyapiurl'}):
            under_test = ClcFirewall(self.module)
            under_test._set_clc_credentials_from_env()
            self.assertEqual(under_test.clc.defaults.ENDPOINT_URL_V2, 'dummyapiurl')


    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcFirewall(self.module)
            under_test._set_clc_credentials_from_env()

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_firewall)
            clc_firewall.ClcFirewall(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')

        # Reset clc_group
        reload(clc_firewall)

    @patch.object(clc_firewall, 'AnsibleModule')
    @patch.object(clc_firewall, 'ClcFirewall')
    def test_main(self, mock_ClcFirewall, mock_AnsibleModule):
        mock_ClcFirewall_instance          = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcFirewall.return_value      = mock_ClcFirewall_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_firewall.main()

        mock_ClcFirewall.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcFirewall_instance.process_request.assert_called_once

if __name__ == '__main__':
    unittest.main()
