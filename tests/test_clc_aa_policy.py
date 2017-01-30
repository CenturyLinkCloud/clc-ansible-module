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
from mock import patch, create_autospec
import os
import unittest

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import clc_ansible_module.clc_aa_policy as clc_aa_policy
from clc_ansible_module.clc_aa_policy import ClcAntiAffinityPolicy


def FakeAnsibleModule():
    module = mock.MagicMock()
    module.check_mode = False
    module.params = {}
    return module


class TestClcAntiAffinityPolicy(unittest.TestCase):

    def setUp(self):
        self.policy_existing = {
            'id': 'existing_id',
            'name': 'existing_name',
            'location': 'existing_loc'
        }

        self.module = FakeAnsibleModule()
        self.module.exit_json = mock.MagicMock()

    def testArgumentSpecContract(self):
        args = ClcAntiAffinityPolicy._define_module_argument_spec()
        self.assertEqual(args, dict(
            name=dict(required=True),
            location=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(default=True)
        ))

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'find_anti_affinity_policy')
    def test_create_no_change(self, mock_find_policy, mock_call_api):
        policy = self.policy_existing
        mock_find_policy.return_value = policy

        under_test = ClcAntiAffinityPolicy(self.module)
        under_test.module.params = {
            'name': policy['name'],
            'location': policy['location'],
            'state': 'present'
        }

        under_test.process_request()

        self.module.exit_json.assert_called_once_with(
            changed=False, policy=policy)

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(ClcAntiAffinityPolicy, '_create_policy')
    @patch.object(clc_common, 'find_anti_affinity_policy')
    def test_create_with_change(self, mock_find_policy, mock_create_policy,
                                mock_call_api):
        policy = self.policy_existing
        mock_find_policy.return_value = None
        mock_create_policy.return_value = policy

        under_test = ClcAntiAffinityPolicy(self.module)
        under_test.module.params = {
            'name': policy['name'],
            'location': policy['location'],
            'state': 'present'
        }

        under_test.process_request()
        self.module.exit_json.assert_called_once_with(
            changed=True, policy=policy)

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'find_anti_affinity_policy')
    def test_delete_no_change(self, mock_find_policy, mock_call_api):
        policy = None
        mock_find_policy.return_value = None

        under_test = ClcAntiAffinityPolicy(self.module)
        under_test.module.params = {
            'name': 'mock_name',
            'location': 'mock_dc',
            'state': 'absent'
        }

        under_test.process_request()

        self.module.exit_json.assert_called_once_with(
            changed=False, policy=None)

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(ClcAntiAffinityPolicy, '_delete_policy')
    @patch.object(clc_common, 'find_anti_affinity_policy')
    def test_delete_with_change(self, mock_find_policy, mock_delete_policy,
                                mock_call_api):
        policy = self.policy_existing
        mock_find_policy.return_value = policy
        mock_delete_policy.return_value = None

        under_test = ClcAntiAffinityPolicy(self.module)
        under_test.module.params = {
            'name': policy['name'],
            'location': policy['location'],
            'state': 'absent'
        }

        under_test.process_request()

        self.module.exit_json.assert_called_once_with(
            changed=True, policy=None)

    @patch.object(clc_aa_policy, 'AnsibleModule')
    @patch.object(clc_aa_policy, 'ClcAntiAffinityPolicy')
    def test_main(self, mock_ClcAAPolicy, mock_AnsibleModule):
        mock_ClcAAPolicy_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcAAPolicy.return_value   = mock_ClcAAPolicy_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_aa_policy.main()

        mock_ClcAAPolicy.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcAAPolicy_instance.process_request.call_count ==1

    @patch.object(clc_common, 'call_clc_api')
    def test_create_aa_policy_error(self, mock_call_api):
        error = ClcApiException(message='Failed')
        mock_call_api.side_effect = error

        under_test = ClcAntiAffinityPolicy(self.module)
        under_test.module.params = {
            'name': 'mock_name',
            'location': 'mock_location',
        }
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        ret = under_test._create_policy()

        self.module.fail_json.assert_called_with(
            msg='Failed to create anti affinity policy: mock_name '
                'in location: mock_location. Failed')

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_aa_policy_error(self, mock_call_api):
        policy = self.policy_existing
        error = ClcApiException(message='Failed')
        mock_call_api.side_effect = error

        under_test = ClcAntiAffinityPolicy(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        ret = under_test._delete_policy(policy)

        self.module.fail_json.assert_called_with(
            msg='Failed to delete anti affinity policy: {name}. '
                'Failed'.format(name=policy['name']))


if __name__ == '__main__':
    unittest.main()
