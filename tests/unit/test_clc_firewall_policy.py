#!/usr/bin/env python
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

import mock
from mock import patch
import unittest

import clc_ansible_module.clc_firewall_policy as clc_firewall_policy
from clc_ansible_module.clc_firewall_policy import ClcFirewallPolicy

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

class TestClcFirewallPolicy(unittest.TestCase):

    def setUp(self):
        self.policy_existing = {
            'id': 'existing_id',
            'status': 'active',
            'enabled': True,
            'source': [
                '1.2.3.0/24',
                '5.6.7.1/32'
                ],
            'destination': [
                '5.6.7.1/32',
                '1.2.3.4/24'
                ],
            'destinationAccount': 'DEST_ALIAS',
            'ports': [
                'any'
                ]
            }

        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

        self.clc_auth = {'v2_api_url': 'https://api.ctl.io/v2/'}

    @patch.object(ClcFirewallPolicy, '_firewall_policies')
    def test_get_firewall_policy_not_exists(self, mock_firewall_policies):
        policy = self.policy_existing
        mock_firewall_policies.return_value = [policy]
        source_account_alias = 'mock_alias'
        location = 'mock_dc'
        firewall_policy_id = 'fake_policy'

        under_test = ClcFirewallPolicy(self.module)

        response = under_test._get_firewall_policy(
            firewall_policy_id, source_account_alias, location)

        self.assertIsNone(response)
        mock_firewall_policies.assert_called_once_with(source_account_alias,
                                                       location)

    @patch.object(ClcFirewallPolicy, '_firewall_policies')
    def test_get_firewall_policy_exists(self, mock_firewall_policies):
        policy = self.policy_existing
        mock_firewall_policies.return_value = [policy]
        source_account_alias = 'mock_alias'
        location = 'mock_dc'
        firewall_policy_id = policy['id']

        under_test = ClcFirewallPolicy(self.module)

        response = under_test._get_firewall_policy(
            firewall_policy_id, source_account_alias, location)

        self.assertEqual(response, policy)
        mock_firewall_policies.assert_called_once_with(source_account_alias,
                                                       location)

    @patch.object(clc_common, 'call_clc_api')
    def test_create_firewall_policy_fail(self, mock_call_api):
        params = {
            'source_account_alias': 'mock_alias',
            'location': 'mock_dc'
        }
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        under_test._create_firewall_policy()

        self.module.fail_json.assert_called_with(
            msg='Unable to create firewall policy for alias: {alias} '
                'in location: {location}. Failed'.format(
                    alias=params['source_account_alias'],
                    location=params['location']))

    @patch.object(clc_common, 'call_clc_api')
    def test_create_firewall_policy_pass(self, mock_call_api):
        params = {
            'source_account_alias': 'mock_alias',
            'location': 'mock_dc',
            'source': ['mock_source'],
            'destination': ['mock_destination'],
            'destination_account_alias': 'mock_dest'
        }
        mock_firewall_response = {'name': 'test', 'id': 'test'}
        mock_call_api.return_value = mock_firewall_response

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        response = under_test._create_firewall_policy()

        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, mock_firewall_response)
        self.assertEqual(mock_call_api.call_count, 1)

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_firewall_policy_exception(self, mock_call_api):
        policy = self.policy_existing
        params = {
            'firewall_policy_id': policy['id'],
            'source_account_alias': 'mock_alias',
            'location': 'mock_dc'
        }
        mock_call_api.side_effect = ClcApiException('Failed')

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        response = under_test._delete_firewall_policy(policy)

        self.module.fail_json.assert_called_with(
            msg='Unable to delete the firewall policy id: {id}. '
                'Failed'.format(id=policy['id']))

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_firewall_policy_policy_exists(self, mock_call_api):
        policy = self.policy_existing
        params = {
            'firewall_policy_id': policy['id'],
            'source_account_alias': 'mock_alias',
            'location': 'mock_dc'
        }
        mock_call_api.return_value = None

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        response = under_test._delete_firewall_policy(policy)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(response, None)
        mock_call_api.assert_called_once_with(
            under_test.module, under_test.clc_auth, 'DELETE',
            '/firewallPolicies/{alias}/{location}/{id}'.format(
                alias=params['source_account_alias'],
                location=params['location'], id=policy['id']))

    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_delete_firewall_policy')
    def test_ensure_firewall_policy_absent_policy_exists(
            self,
            mock_delete_firewall_policy,
            mock_get_firewall_policy):
        policy = self.policy_existing
        params = {
            'firewall_policy_id': policy['id']
        }
        mock_get_firewall_policy.return_value = policy
        mock_delete_firewall_policy.return_value = None

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, policy_id, response = \
            under_test._ensure_firewall_policy_is_absent()

        self.assertTrue(changed, True)
        self.assertEqual(policy_id, policy['id'])
        self.assertEqual(response, None)
        mock_get_firewall_policy.assert_called_once_with(policy['id'])
        mock_delete_firewall_policy.assert_called_once_with(policy)

    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_delete_firewall_policy')
    def test_ensure_firewall_policy_absent_policy_not_exist(
            self,
            mock_delete_firewall_policy,
            mock_get_firewall_policy):
        policy = self.policy_existing
        params = {
            'firewall_policy_id': 'fake_policy'
        }
        mock_get_firewall_policy.return_value = None

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, policy_id, response = \
            under_test._ensure_firewall_policy_is_absent()

        self.assertFalse(changed)
        self.assertEqual(policy_id, 'fake_policy')
        self.assertEqual(response, None)
        mock_get_firewall_policy.assert_called_once_with('fake_policy')
        self.assertFalse(mock_delete_firewall_policy.called)

    @patch.object(ClcFirewallPolicy, '_wait_for_requests_to_complete')
    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_policy_matches_request')
    @patch.object(ClcFirewallPolicy, '_update_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_create_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_get_policy_id_from_response')
    def test_ensure_firewall_policy_present_policy_exists_update(
            self,
            mock_get_policy_id_from_response,
            mock_create_firewall_policy,
            mock_update_firewall_policy,
            mock_policy_matches,
            mock_get_firewall_policy,
            mock_wait):
        policy = self.policy_existing
        params = {
            'firewall_policy_id': policy['id'],
            'source_account_alias': 'mock_alias',
            'location': 'mock_dc',
            'ports': 'mock_ports'
        }
        mock_get_policy_id_from_response.return_value = policy['id']
        mock_update_firewall_policy.return_value = policy
        mock_get_firewall_policy.return_value = policy
        mock_policy_matches.return_value = False
        mock_wait.return_value = policy

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, policy_id, response = \
            under_test._ensure_firewall_policy_is_present()

        self.assertTrue(changed)
        self.assertEqual(policy_id, policy['id'])
        self.assertFalse(self.module.fail_json.called)
        mock_get_firewall_policy.assert_called_with(policy['id'])
        self.assertFalse(mock_create_firewall_policy.called)
        mock_update_firewall_policy.assert_called_once_with(policy)

    @patch.object(ClcFirewallPolicy, '_wait_for_requests_to_complete')
    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_policy_matches_request')
    @patch.object(ClcFirewallPolicy, '_update_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_create_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_get_policy_id_from_response')
    def test_ensure_firewall_policy_present_policy_exists_no_update(
            self,
            mock_get_policy_id_from_response,
            mock_create_firewall_policy,
            mock_update_firewall_policy,
            mock_policy_matches,
            mock_get_firewall_policy,
            mock_wait):
        policy = self.policy_existing
        params = {
            'firewall_policy_id': policy['id'],
            'source_account_alias': 'mock_alias',
            'location': 'mock_dc',
            'ports': 'mock_ports'
        }
        mock_get_policy_id_from_response.return_value = policy['id']
        mock_update_firewall_policy.return_value = policy
        mock_get_firewall_policy.return_value = policy
        mock_policy_matches.return_value = True
        mock_wait.return_value = policy

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, policy_id, response = \
            under_test._ensure_firewall_policy_is_present()

        self.assertFalse(changed)
        self.assertEqual(policy_id, policy['id'])
        self.assertFalse(self.module.fail_json.called)
        mock_get_firewall_policy.assert_called_with(policy['id'])
        self.assertFalse(mock_create_firewall_policy.called)
        self.assertFalse(mock_update_firewall_policy.called)

    @patch.object(ClcFirewallPolicy, '_wait_for_requests_to_complete')
    @patch.object(ClcFirewallPolicy, '_find_matching_policy')
    @patch.object(ClcFirewallPolicy, '_update_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_create_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_get_policy_id_from_response')
    def test_ensure_firewall_policy_present_policy_not_exist(
            self,
            mock_get_policy_id_from_response,
            mock_create_firewall_policy,
            mock_update_firewall_policy,
            mock_find_matching_policy,
            mock_wait):
        policy = self.policy_existing
        params = {
            'source_account_alias': 'mock_alias',
            'location': 'mock_dc',
            'ports': 'mock_ports'
        }
        mock_create_firewall_policy.return_value = policy
        mock_get_policy_id_from_response.return_value = policy['id']
        mock_find_matching_policy.return_value = None
        mock_wait.return_value = policy

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, policy_id, response = \
            under_test._ensure_firewall_policy_is_present()

        self.assertTrue(changed)
        self.assertEqual(policy_id, policy['id'])
        self.assertFalse(self.module.fail_json.called)
        self.assertTrue(mock_create_firewall_policy.called)
        self.assertFalse(mock_update_firewall_policy.called)

    @patch.object(ClcFirewallPolicy, '_update_firewall_policy')
    @patch.object(ClcFirewallPolicy, '_find_matching_policy')
    @patch.object(ClcFirewallPolicy, '_get_policy_id_from_response')
    def test_ensure_firewall_policy_present_destination_not_supported(
            self,
            mock_get_policy_id_from_response,
            mock_find_matching_policy,
            mock_update_policy):
        policy = self.policy_existing
        params = {
            'source_account_alias': 'mock_alias',
            'location': 'mock_dc',
            'enabled': policy['enabled'],
            'source': policy['source'],
            'destination': policy['destination'],
            'destination_account_alias': 'new_destination',
            'wait': True
        }

        mock_get_policy_id_from_response.return_value = policy['id']
        mock_find_matching_policy.return_value = policy

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        under_test._ensure_firewall_policy_is_present()

        self.module.fail_json.assert_called_with(
            msg='Changing destination alias from: {orig} to: {new} '
                'is not supported.'.format(
                    orig=policy['destinationAccount'],
                    new=params['destination_account_alias']))

    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    def test_update_policy_w_no_policy_exist(self, mock_get):
        mock_get.return_value = None
        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = {'firewall_policy_id': 'something'}
        under_test._ensure_firewall_policy_is_present()
        self.module.fail_json.assert_called_with(msg='Unable to find the firewall policy id: something')

    @patch.object(clc_common, 'call_clc_api')
    def test_update_firewall_policy_pass(self, mock_call_api):
        policy = self.policy_existing
        mock_call_api.return_value = None
        params = {
            'source_account_alias': 'mock_alias',
            'location': 'mock_dc',
            'enabled': True,
            'source': '12345',
            'destination': '12345',
            'ports': 'any',
        }

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        response = under_test._update_firewall_policy(policy)

        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(mock_call_api.call_count, 1)

    @patch.object(clc_common, 'call_clc_api')
    def test_update_firewall_policy_fail(self, mock_call_api):
        policy = self.policy_existing
        params = {
            'source_account_alias': 'mock_alias',
            'location': 'mock_dc',
            'enabled': True,
            'source': '12345',
            'destination': '12345',
            'ports': 'any'
        }
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        under_test._update_firewall_policy(policy)

        self.module.fail_json.assert_called_with(
            msg='Unable to update the firewall policy id: {id}. Failed'.format(
                id=policy['id']))

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
    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'call_clc_api')
    def test_process_request_state_present(self,
                                           mock_call_api,
                                           mock_authenticate,
                                           mock_ensure_present):
        params = {
            'state': 'present',
            'location': 'test',
            'source': ['1','2'],
            'destination': ['1','2'],
            'source_account_alias': 'alias',
            'destination_account_alias': 'alias',
            'wait': True
        }
        mock_authenticate.return_value = self.clc_auth
        mock_ensure_present.return_value = True, 'mock_id', {}

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        under_test.process_request()

        self.assertTrue(self.module.exit_json.called)
        self.module.exit_json.assert_called_once_with(
            changed=True, firewall_policy_id='mock_id', firewall_policy={})
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcFirewallPolicy, '_ensure_firewall_policy_is_absent')
    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'call_clc_api')
    def test_process_request_state_absent(self,
                                          mock_call_api,
                                          mock_authenticate,
                                          mock_ensure_absent):
        params = {
            'firewall_policy_id': 'mock_id',
            'state': 'absent',
            'location': 'test',
            'source': ['1','2'],
            'destination': ['1','2'],
            'source_account_alias': 'alias',
            'destination_account_alias': 'alias',
            'wait': True
        }
        mock_authenticate.return_value = self.clc_auth
        mock_ensure_absent.return_value = True, 'mock_id', None

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        under_test.process_request()

        # Assert
        self.assertTrue(self.module.exit_json.called)
        self.module.exit_json.assert_called_once_with(
            changed=True, firewall_policy_id='mock_id', firewall_policy=None)
        self.assertFalse(self.module.fail_json.called)

    def test_policy_matches_request_true(self):
        policy = self.policy_existing
        params = {
            'destination_account_alias': policy['destinationAccount'],
            'enabled': policy['enabled'],
            'source': policy['source'],
            'destination': policy['destination'],
            'ports': policy['ports'],
            'wait': True
        }

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        res = under_test._policy_matches_request(policy)

        self.assertTrue(res)



    def test_policy_matches_request_false_source(self):
        policy = self.policy_existing
        params = {
            'source': ['new_source'],
            'wait': True
        }

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        res = under_test._policy_matches_request(policy)

        self.assertFalse(res)

    def test_policy_matches_request_false_dest(self):
        policy = self.policy_existing
        params = {
            'destination': ['new_destination'],
            'wait': True
        }

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        res = under_test._policy_matches_request(policy)

        self.assertFalse(res)

    def test_policy_matches_request_false_ports(self):
        policy = self.policy_existing
        params = {
            'ports': ['new_ports'],
            'wait': True
        }

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        res = under_test._policy_matches_request(policy)

        self.assertFalse(res)

    def test_policy_matches_request_false_enabled(self):
        policy = self.policy_existing
        params = {
            'enabled': False,
            'wait': True
        }

        under_test = ClcFirewallPolicy(self.module)
        under_test.module.params = params

        res = under_test._policy_matches_request(policy)

        self.assertFalse(res)

    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    def test_wait_for_requests_to_complete_pending(self, mock_get):
        mock_pending_status = {
            'status': 'pending'
        }
        mock_get.return_value = mock_pending_status
        under_test = ClcFirewallPolicy(self.module)
        under_test._wait_for_requests_to_complete('firewall_pol_id',
                                                  wait_limit=0, poll_freq=0)
        self.assertTrue(under_test._get_firewall_policy.called)

    @patch.object(ClcFirewallPolicy, '_get_firewall_policy')
    def test_wait_for_requests_to_complete_active(self, mock_get):
        mock_pending_status = {
            'status': 'active'
        }
        mock_get.return_value = mock_pending_status
        under_test = ClcFirewallPolicy(self.module)
        under_test._wait_for_requests_to_complete('firewall_pol_id',
                                                  wait_limit=0, poll_freq=0)
        self.assertTrue(under_test._get_firewall_policy.called)

if __name__ == '__main__':
    unittest.main()
