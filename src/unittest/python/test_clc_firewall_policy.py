#!/usr/bin/python
# Copyright 2015 CenturyLink
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import clc_ansible_module.clc_firewall_policy as clc_firewall_policy
from clc_ansible_module.clc_firewall_policy import ClcFirewallPolicy

from clc import APIFailedResponse

import mock
from mock import patch
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

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_firewall_policy)
            ClcFirewallPolicy(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')
        reload(clc_firewall_policy)

    def test_requests_invalid_version(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'requests':
                args[0]['requests'].__version__ = '2.4.0'
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_firewall_policy)
            ClcFirewallPolicy(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library  version should be >= 2.5.0')
        reload(clc_firewall_policy)

    def test_requests_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'requests':
                args[0]['requests'].__version__ = '2.7.0'
                raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_firewall_policy)
            ClcFirewallPolicy(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library is required for this module')
        reload(clc_firewall_policy)

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_get_firewall_policy_fail(self, mock_clc_sdk):
        source_account_alias = 'WFAD'
        location = 'VA1'
        firewall_policy = 'fake_policy'

        error = APIFailedResponse()
        error.response_status_code = 500
        error.response_text = 'mock failure message'
        mock_clc_sdk.v2.API.Call.side_effect = error
        test_firewall_policy = ClcFirewallPolicy(self.module)
        response = test_firewall_policy._get_firewall_policy(
            source_account_alias, location, firewall_policy)
        self.module.fail_json.assert_called_with(msg='Unable to fetch the firewall policy with id : fake_policy. mock failure message')

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_get_firewall_policy_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        source_account_alias = 'WFAD'
        location = 'WA1'
        firewall_policy = 'test_policy'

        test_firewall = ClcFirewallPolicy(self.module)
        response = test_firewall._get_firewall_policy(
            source_account_alias, location, firewall_policy)
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
        error = APIFailedResponse()
        error.response_text = 'Mock failure message'
        mock_clc_sdk.v2.API.Call.side_effect = error
        test_firewall_policy = ClcFirewallPolicy(self.module)
        test_firewall_policy._create_firewall_policy(
            source_account_alias,
            location,
            payload)
        self.module.fail_json.assert_called_with(msg='Unable to create firewall policy. Mock failure message')

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
        assert test_firewall.clc.v2.API.Call.call_count == 1

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_delete_firewall_policy_fail(self, mock_clc_sdk):
        source_account_alias = 'WFAD'
        location = 'wa1'
        firewall_policy_id = 'this_is_not_a_real_policy'
        error = APIFailedResponse()
        error.response_text = 'Mock failure message'
        mock_clc_sdk.v2.API.Call.side_effect = error
        test_firewall_policy = ClcFirewallPolicy(self.module)
        test_firewall_policy._delete_firewall_policy(
            source_account_alias,
            location,
            firewall_policy_id)
        self.module.fail_json.assert_called_with(msg='Unable to delete the firewall policy id : this_is_not_a_real_policy. Mock failure message')

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

    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    def test_ensure_firewall_policy_absent_fail(self, mock_get):
        source_account_alias = 'WFAD'
        location = 'wa1'
        payload = {
            'destinationAccount': 'wfas',
            'source': '12345',
            'destination': '12345',
            'ports': 'any',
            'firewall_policy_id': 'this_is_not_a_real_policy'
        }
        mock_get.return_value = None
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

        mock_get_firewall_policy.return_value = 'result'
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

    @mock.patch.object(ClcFirewallPolicy, '_wait_for_requests_to_complete')
    @mock.patch.object(ClcFirewallPolicy, '_compare_get_request_with_dict')
    @mock.patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    @mock.patch.object(ClcFirewallPolicy, '_update_firewall_policy')
    @mock.patch.object(ClcFirewallPolicy, '_get_policy_id_from_response')
    def test_ensure_firewall_policy_present_pass(
            self,
            mock_get_policy_id_from_response,
            mock_update_firewall_policy,
            mock_get_firewall_policy,
            mock_compare_get_request_with_dict,
            mock_wait):
        source_account_alias = 'WFAD'
        location = 'VA1'
        firewall_dict = {'firewall_policy_id': 'something'}

        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_get_policy_id_from_response.return_value = firewall_dict
        mock_update_firewall_policy.return_value = mock_firewall_response
        mock_get_firewall_policy.return_value = firewall_dict
        mock_compare_get_request_with_dict.return_value = True
        mock_wait.return_value = 'OK'

        self.module.check_mode = False
        test_firewall = ClcFirewallPolicy(self.module)

        changed, policy_id, response = test_firewall._ensure_firewall_policy_is_present(
            source_account_alias, location, firewall_dict)

        self.assertFalse(self.module.fail_json.called)
        self.assertTrue(changed)
        self.assertEqual(policy_id, 'something')
        mock_update_firewall_policy.assert_called_once_with(
            source_account_alias,
            location,
            'something',
            firewall_dict)
        mock_get_firewall_policy.assert_called_with(
            source_account_alias,
            location,
            'something')

    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    def test_update_policy_w_no_policy_exist(self, mock_get):
        mock_get.return_value = None
        firewall_dict = {'firewall_policy_id': 'something'}
        under_test = ClcFirewallPolicy(self.module)
        under_test._ensure_firewall_policy_is_present(
            'alias',
            'location',
            firewall_dict)
        self.module.fail_json.assert_called_with(msg='Unable to find the firewall policy id : something')

    @patch.object(ClcFirewallPolicy, '_wait_for_requests_to_complete')
    @patch.object(ClcFirewallPolicy, '_get_policy_id_from_response')
    @patch.object(ClcFirewallPolicy, '_create_firewall_policy')
    def test_create_policy_w_changed(self, mock_create, mock_get, mock_wait):
        mock_create.return_value = 'SUCCESS'
        mock_get.return_value = 'policy1'
        mock_wait.return_value = 'OK'
        firewall_dict = {'firewall_policy_id': None}
        self.module.check_mode = False
        under_test = ClcFirewallPolicy(self.module)
        changed, firewall_policy_id, response = under_test._ensure_firewall_policy_is_present(
            'alias',
            'location',
            firewall_dict)
        self.assertEqual(changed, True)
        self.assertEqual(firewall_policy_id, 'policy1')
        self.assertEqual(response, 'OK')

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_update_firewall_policy_pass(self, mock_clc_sdk):
        mock_firewall_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_firewall_response
        firewall_dict = {
            'source': '12345',
            'destination': '12345',
            'ports': 'any',
            'destination_account_alias': 'wfas'
        }

        test_firewall = ClcFirewallPolicy(self.module)
        response = test_firewall._update_firewall_policy(
            source_account_alias='WFAD',
            location='WA1',
            firewall_policy_id='fake_policy',
            firewall_dict=firewall_dict)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, mock_firewall_response)
        assert test_firewall.clc.v2.API.Call.call_count == 1

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_update_firewall_policy_fail(self, mock_clc_sdk):
        source_account_alias = 'WFAD'
        location = 'VA1'
        firewall_policy_id = 'mock policy id'
        payload = {
            'destinationAccount': 'wfas',
            'source': '12345',
            'destination': '12345',
            'ports': 'any'
        }
        error = APIFailedResponse()
        error.response_text = 'Mock failure message'
        mock_clc_sdk.v2.API.Call.side_effect = error
        test_firewall_policy = ClcFirewallPolicy(self.module)
        test_firewall_policy._update_firewall_policy(
            source_account_alias,
            location,
            firewall_policy_id,
            firewall_policy_id)
        self.module.fail_json.assert_called_with(msg='Unable to update the firewall policy id : mock policy id. Mock failure message')

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

    @patch.object(clc_firewall_policy, 'AnsibleModule')
    @patch.object(clc_firewall_policy, 'ClcFirewallPolicy')
    def test_main(self, mock_ClcFirewallPolicy, mock_AnsibleModule):
        mock_ClcFirewallPolicy_instance = mock.MagicMock()
        mock_AnsibleModule_instance = mock.MagicMock()
        mock_ClcFirewallPolicy.return_value = mock_ClcFirewallPolicy_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_firewall_policy.main()

        mock_ClcFirewallPolicy.assert_called_once_with(
            mock_AnsibleModule_instance)
        assert mock_ClcFirewallPolicy_instance.process_request.call_count == 1


    @patch.object(ClcFirewallPolicy, '_ensure_firewall_policy_is_present')
    @patch.object(ClcFirewallPolicy, '_set_clc_credentials_from_env')
    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_process_request_state_present(self,
                                           mock_clc_sdk,
                                           mock_set_clc_creds,
                                           mock_ensure_present):
        # Setup Test
        self.module.params = {
            'state': 'present',
            'location': 'test',
            'source': ['1','2'],
            'destination': ['1','2'],
            'source_account_alias': 'alias',
            'destination_account_alias': 'alias',
            'wait': True
        }
        changed = False
        policy_id = None

        mock_ensure_present.return_value = True, '123', {}
        # Test
        under_test = ClcFirewallPolicy(self.module)
        under_test.process_request()

        # Assert
        self.assertTrue(self.module.exit_json.called)
        self.module.exit_json.assert_called_once_with(changed=True, firewall_policy_id='123', firewall_policy={})
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcFirewallPolicy, '_ensure_firewall_policy_is_present')
    @patch.object(ClcFirewallPolicy, '_set_clc_credentials_from_env')
    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_process_request_state_absent(self,
                                           mock_clc_sdk,
                                           mock_set_clc_creds,
                                           mock_ensure_absent):
        # Setup Test
        self.module.params = {
            'state': 'absent',
            'location': 'test',
            'source': ['1','2'],
            'destination': ['1','2'],
            'source_account_alias': 'alias',
            'destination_account_alias': 'alias',
            'wait': True
        }
        changed = False
        policy_id = None

        mock_ensure_absent.return_value = True, '123', {}
        # Test
        under_test = ClcFirewallPolicy(self.module)
        under_test.process_request()

        # Assert
        self.assertTrue(self.module.exit_json.called)
        self.module.exit_json.assert_called_once_with(changed=True, firewall_policy_id=None, firewall_policy=[])
        self.assertFalse(self.module.fail_json.called)

    def test_compare_get_request_with_dict_false(self):
        under_test = ClcFirewallPolicy
        # Setup Test
        self.module.params = {
            'state': 'invalid',
            'location': 'test',
            'source': ['1','2'],
            'destination': ['1','2'],
            'source_account_alias': 'alias',
            'destination_account_alias': 'alias',
            'wait': True
        }
        firewall_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destination_account_alias': 'wfad',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present'
        }
        response_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destinationAccount': 'wfad',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present',
            'enabled': True
        }
        # Test
        under_test = ClcFirewallPolicy(self.module)
        res = under_test._compare_get_request_with_dict(response_dict, firewall_dict)
        self.assertEqual(res, False)

    def test_compare_get_request_with_dict_true_source(self):
        under_test = ClcFirewallPolicy
        # Setup Test
        self.module.params = {
            'state': 'invalid',
            'location': 'test',
            'source': ['1','2'],
            'destination': ['1','2'],
            'source_account_alias': 'alias',
            'destination_account_alias': 'alias',
            'wait': True
        }
        firewall_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destination_account_alias': 'wfad',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present'
        }
        response_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destinationAccount': 'wfad',
            'source': ['10.121.41.0/22', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present',
            'enabled': True
        }
        # Test
        under_test = ClcFirewallPolicy(self.module)
        res = under_test._compare_get_request_with_dict(response_dict, firewall_dict)
        self.assertEqual(res, True)

    def test_compare_get_request_with_dict_true_dest(self):
        under_test = ClcFirewallPolicy
        # Setup Test
        self.module.params = {
            'state': 'invalid',
            'location': 'test',
            'source': ['1','2'],
            'destination': ['1','2'],
            'source_account_alias': 'alias',
            'destination_account_alias': 'alias',
            'wait': True
        }
        firewall_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destination_account_alias': 'wfad',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present'
        }
        response_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destinationAccount': 'wfad',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/22', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present',
            'enabled': True
        }
        # Test
        under_test = ClcFirewallPolicy(self.module)
        res = under_test._compare_get_request_with_dict(response_dict, firewall_dict)
        self.assertEqual(res, True)

    def test_compare_get_request_with_dict_true_ports(self):
        under_test = ClcFirewallPolicy
        # Setup Test
        self.module.params = {
            'state': 'invalid',
            'location': 'test',
            'source': ['1','2'],
            'destination': ['1','2'],
            'source_account_alias': 'alias',
            'destination_account_alias': 'alias',
            'wait': True
        }
        firewall_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destination_account_alias': 'wfad',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present'
        }
        response_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destinationAccount': 'wfad',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['none'],
            'state': 'present',
            'enabled': True
        }
        # Test
        under_test = ClcFirewallPolicy(self.module)
        res = under_test._compare_get_request_with_dict(response_dict, firewall_dict)
        self.assertEqual(res, True)

    def test_compare_get_request_with_dict_true_acct_alias(self):
        under_test = ClcFirewallPolicy
        # Setup Test
        self.module.params = {
            'state': 'invalid',
            'location': 'test',
            'source': ['1','2'],
            'destination': ['1','2'],
            'source_account_alias': 'alias',
            'destination_account_alias': 'alias',
            'wait': True
        }
        firewall_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destination_account_alias': 'wfad',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present'
        }
        response_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destinationAccount': 'nothing',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present',
            'enabled': True
        }
        # Test
        under_test = ClcFirewallPolicy(self.module)
        res = under_test._compare_get_request_with_dict(response_dict, firewall_dict)
        self.assertEqual(res, True)

    def test_compare_get_request_with_dict_true_enabled(self):
        under_test = ClcFirewallPolicy
        # Setup Test
        self.module.params = {
            'state': 'invalid',
            'location': 'test',
            'source': ['1','2'],
            'destination': ['1','2'],
            'source_account_alias': 'alias',
            'destination_account_alias': 'alias',
            'wait': True
        }
        firewall_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'source_account_alias': 'wfad',
            'destination_account_alias': 'wfad',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present',
            'enabled': True
        }
        response_dict = {
            'firewall_policy_id': '61a18d1e3498408d8d20a486c1a47178',
            'sourceAccount': 'wfad',
            'destinationAccount': 'wfad',
            'source': ['10.121.41.0/24', '10.122.124.0/24'],
            'destination': ['10.121.41.0/24', '10.122.124.0/24'],
            'wait': True,
            'ports': ['any'],
            'state': 'present',
            'enabled': False
        }
        # Test
        under_test = ClcFirewallPolicy(self.module)
        res = under_test._compare_get_request_with_dict(response_dict, firewall_dict)
        self.assertEqual(res, True)

    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    def test_wait_for_requests_to_complete_pending(self, mock_get):
        mock_pending_status = {
            'status': 'pending'
        }
        mock_get.return_value = mock_pending_status
        under_test = ClcFirewallPolicy(self.module)
        under_test._wait_for_requests_to_complete('alias', 'location', 'firewall_pol_id', 2)
        self.assertTrue(under_test._get_firewall_policy.called)

    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    def test_wait_for_requests_to_complete_active(self, mock_get):
        mock_pending_status = {
            'status': 'active'
        }
        mock_get.return_value = mock_pending_status
        under_test = ClcFirewallPolicy(self.module)
        under_test._wait_for_requests_to_complete('alias', 'location', 'firewall_pol_id', 2)
        self.assertTrue(under_test._get_firewall_policy.called)

    @patch.object(clc_firewall_policy, 'clc_sdk')
    def test_set_user_agent(self, mock_clc_sdk):
        clc_firewall_policy.__version__ = "1"
        ClcFirewallPolicy._set_user_agent(mock_clc_sdk)
        self.assertTrue(mock_clc_sdk.SetRequestsSession.called)

if __name__ == '__main__':
    unittest.main()
