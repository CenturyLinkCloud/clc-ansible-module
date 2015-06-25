#!/usr/bin/python


import clc_ansible_module.clc_firewall_policy as clc_firewall_policy
from clc_ansible_module.clc_firewall_policy import ClcFirewallPolicy

import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch
from mock import create_autospec
import unittest


class TestClcFirewallPolicy(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(clc_firewall_policy, 'clc_sdk') as mock_clc_sdk:
                under_test = ClcFirewallPolicy(self.module)
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
        test_firewall_policy = ClcFirewallPolicy(self.module)
        response, success = test_firewall_policy._get_firewall_policy(
            source_account_alias, location, firewall_policy)
        self.assertFalse(success)

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_get_firewall_policy_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        source_account_alias = 'WFAD'
        location = 'WA1'
        firewall_policy = 'test_policy'

        test_firewall = ClcFirewallPolicy(self.module)
        response, success = test_firewall._get_firewall_policy(
            source_account_alias, location, firewall_policy)
        self.assertTrue(success)
        self.assertEqual(response, mock_firewall_response)
        test_firewall.clc.v2.API.Call.assert_called_once_with(
            'GET',
            '/v2-experimental/firewallPolicies/WFAD/WA1/test_policy')


    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_create_firewall_policy_fail(self, mock_clc_sdk):
        source_account_alias = 'WFAD'
        location = 'VA1'
        payload = {
            'destinationAccount': 'wfas',
            'source': '12345',
            'destination': '12345',
            'ports': 'any'
        }
        mock_clc_sdk.v2.API.Call.side_effect = OSError('Failed')
        test_firewall_policy = ClcFirewallPolicy(self.module)

        self.assertRaises(OSError, test_firewall_policy._create_firewall_policy, source_account_alias, location, payload)

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_create_firewall_policy_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        firewall_dict = {
            'source': '12345',
            'destination': '12345',
            'ports': 'any',
            'destination_account_alias': 'wfas'
        }

        test_firewall = ClcFirewallPolicy(self.module)
        response = test_firewall._create_firewall_policy(
            source_account_alias='WFAD',
            location='WA1',
            firewall_dict=firewall_dict)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, mock_firewall_response)
        test_firewall.clc.v2.API.Call.assert_called_once

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_delete_firewall_policy_fail(self, mock_clc_sdk):
        source_account_alias = 'WFAD'
        location = 'wa1'
        firewall_policy_id = 'this_is_not_a_real_policy'

        mock_clc_sdk.v2.API.Call.side_effect = OSError('Failed')
        test_firewall_policy = ClcFirewallPolicy(self.module)

        self.assertRaises(OSError, test_firewall_policy._delete_firewall_policy, source_account_alias, location, firewall_policy_id)

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_delete_firewall_policy_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        source_account_alias = 'WFAD'
        location = 'wa1'
        firewall_policy = 'this_is_not_a_real_policy'

        test_firewall = ClcFirewallPolicy(self.module)
        response = test_firewall._delete_firewall_policy(
            source_account_alias,
            location,
            firewall_policy)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, mock_firewall_response)
        test_firewall.clc.v2.API.Call.assert_called_once_with(
            'DELETE', '/v2-experimental/firewallPolicies/%s/%s/%s' %
            (source_account_alias, location, firewall_policy))

    def test_ensure_firewall_policy_absent_fail(self):
        source_account_alias = 'WFAD'
        location = 'wa1'
        payload = {
            'destinationAccount': 'wfas',
            'source': '12345',
            'destination': '12345',
            'ports': 'any',
            'firewall_policy_id': 'this_is_not_a_real_policy'
        }
        test_firewall_policy = ClcFirewallPolicy(self.module)
        changed, policy, response = test_firewall_policy._ensure_firewall_policy_is_absent(
            source_account_alias, location, payload)
        self.assertFalse(changed)

    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_delete_firewall_policy')
    def test_ensure_firewall_policy_absent_pass(
            self,
            mock_delete_firewall_policy,
            mock_get_firewall_policy):
        source_account_alias = 'WFAD'
        location = 'WA1'
        firewall_dict = {'firewall_policy_id': 'something'}
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]

        mock_get_firewall_policy.return_value = 'result', True
        mock_delete_firewall_policy.return_value = mock_firewall_response
        self.module.check_mode = False

        test_firewall = ClcFirewallPolicy(self.module)
        changed, policy_id, response = test_firewall._ensure_firewall_policy_is_absent(
            source_account_alias, location, firewall_dict)
        self.assertTrue(changed, True)
        self.assertEqual(policy_id, 'something')
        self.assertEqual(response, mock_firewall_response)
        mock_get_firewall_policy.assert_called_once_with(
            source_account_alias,
            location,
            'something')
        mock_delete_firewall_policy.assert_called_once_with(
            source_account_alias,
            location,
            'something')

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_ensure_firewall_policy_present_fail(self, mock_clc_sdk):
        source_account_alias = 'WFAD'
        location = 'wa1'
        payload = {
            'destinationAccount': 'wfas',
            'source': '12345',
            'destination': '12345',
            'ports': 'any',
            'firewall_policy_id': 'this_is_not_a_real_policy'
        }
        self.module.check_mode = False

        mock_clc_sdk.v2.API.Call.side_effect = OSError('Failed')
        test_firewall_policy = ClcFirewallPolicy(self.module)

        self.assertRaises(OSError, test_firewall_policy._ensure_firewall_policy_is_present, source_account_alias, location, payload)

    @mock.patch.object(ClcFirewallPolicy, '_create_firewall_policy')
    @mock.patch.object(ClcFirewallPolicy, '_get_policy_id_from_response')
    def test_ensure_firewall_policy_present_pass(
            self,
            mock_get_policy_id_from_response,
            mock_create_firewall_policy):
        source_account_alias = 'WFAD'
        location = 'VA1'
        firewall_dict = {'firewall_policy_id': 'something'}

        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_get_policy_id_from_response.return_value = 'fake_policy'
        mock_create_firewall_policy.return_value = mock_firewall_response

        self.module.check_mode = False
        test_firewall = ClcFirewallPolicy(self.module)

        changed, policy_id, response = test_firewall._ensure_firewall_policy_is_present(
            source_account_alias, location, firewall_dict)

        self.assertFalse(self.module.fail_json.called)
        self.assertTrue(changed)
        self.assertEqual(policy_id, 'fake_policy')
        mock_create_firewall_policy.assert_called_once_with(
            source_account_alias,
            location,
            firewall_dict)
        mock_get_policy_id_from_response.assert_called_once_with(
            mock_firewall_response)

    @patch.object(clc_firewall_policy, 'clc_sdk')
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
        test_firewall = ClcFirewallPolicy(self.module)
        changed, policy_id, response = test_firewall._ensure_firewall_policy_is_present(
            source_account_alias, location, firewall_dict)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, mock_firewall_response)
        test_firewall.clc.v2.API.Call.assert_called_once_with(
            'PUT', '/v2-experimental/firewallPolicies/%s/%s/%s' %
            (source_account_alias, location, test_firewall_policy), firewall_dict)

    def test_get_policy_id_from_response(self):
        test_policy_id = 'test_policy_id'
        test_response = {
            "links": [
                {
                    "rel": "self",
                    "href": "http://api.ctl.io/v2-experimental/firewallPolicies/wfad/va1/" +
                    test_policy_id,
                    "verbs": [
                        "GET",
                        "PUT",
                        "DELETE"]}]}
        test_firewall = ClcFirewallPolicy(self.module)
        policy_id = test_firewall._get_policy_id_from_response(test_response)
        self.assertEqual(policy_id, test_policy_id)

    def test_define_argument_spec(self):
        result = ClcFirewallPolicy._define_module_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(ClcFirewallPolicy, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            under_test = ClcFirewallPolicy(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcFirewallPolicy, 'clc')
    def test_set_clc_credentials_w_api_url(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_URL': 'dummyapiurl'}):
            under_test = ClcFirewallPolicy(self.module)
            under_test._set_clc_credentials_from_env()
            self.assertEqual(
                under_test.clc.defaults.ENDPOINT_URL_V2,
                'dummyapiurl')

    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcFirewallPolicy(self.module)
            under_test._set_clc_credentials_from_env()

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__

        def mock_import(name, *args):
            if name == 'clc':
                raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_firewall_policy)
            clc_firewall_policy.ClcFirewallPolicy(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(
            msg='clc-python-sdk required for this module')

        # Reset clc_group
        reload(clc_firewall_policy)

    @patch.object(clc_firewall_policy, 'AnsibleModule')
    @patch.object(clc_firewall_policy, 'ClcFirewallPolicy')
    def test_main(self, mock_ClcFirewallPolicy, mock_AnsibleModule):
        mock_ClcFirewallPolicy_instance = mock.MagicMock()
        mock_AnsibleModule_instance = mock.MagicMock()
        mock_ClcFirewallPolicy.return_value = mock_ClcFirewallPolicy_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_firewall_policy.main()

        mock_ClcFirewallPolicy.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcFirewallPolicy_instance.process_request.assert_called_once

if __name__ == '__main__':
    unittest.main()
