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
import os
import unittest

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import clc_ansible_module.clc_alert_policy as clc_alert_policy
from clc_ansible_module.clc_alert_policy import ClcAlertPolicy

# This is a pretty brute-force attack at unit testing.
# This is my first stab, so anyone reading this who is more Python-inclined
# is both welcome and encouraged to make it better.

def FakeAnsibleModule():
    module = mock.MagicMock()
    module.check_mode = False
    module.params = {}
    return module

class TestClcAlertPolicy(unittest.TestCase):

    def setUp(self):
        self.module = FakeAnsibleModule()
        self.module.exit_json = mock.MagicMock()

        self.policy_existing = {
            "id": "51db33be37b040f6a135abbaf989e36a",
            "name": "alert1",
            "actions": [
                {"action": "email",
                 "settings": {
                     "recipients": [
                         "test1@centurylink.com",
                         "test2@centurylink.com"
                     ]}
                 }
            ],
            "triggers": [
                {"metric": "disk",
                 "duration": "00:05:00",
                 "threshold": 5.0}
            ]
        }

    @patch.object(clc_alert_policy, 'AnsibleModule')
    @patch.object(clc_alert_policy, 'ClcAlertPolicy')
    def test_main(self, mock_ClcAlertPolicy, mock_AnsibleModule):
        mock_ClcAlertPolicy_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcAlertPolicy.return_value   = mock_ClcAlertPolicy_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_alert_policy.main()

        mock_ClcAlertPolicy.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcAlertPolicy_instance.process_request.call_count == 1

    @patch.object(ClcAlertPolicy, '_ensure_alert_policy_is_present')
    @patch.object(clc_common, 'call_clc_api')
    def test_process_request_state_present(self, mock_call_api,
                                           mock_ensure_alert_policy):
        policy = self.policy_existing
        test_params = {
            'name': policy['name'],
            'alias': 'testalias',
            'state': 'present'
        }
        mock_ensure_alert_policy.return_value = True, 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True,
                                                      policy='success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_ensure_alert_policy_is_absent')
    @patch.object(clc_common, 'call_clc_api')
    def test_process_request_state_absent(self, mock_call_api,
                                          mock_ensure_alert_policy):
        test_params = {
            'name': 'testname',
            'alias': 'testalias',
            'state': 'absent'
        }
        mock_ensure_alert_policy.return_value = True, None

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True, policy=None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_create_alert_policy')
    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'call_clc_api')
    def test_ensure_alert_policy_is_present_new(self, mock_call_api,
                                                mock_find_policy,
                                                mock_create):
        test_params = {
            'name': 'testname',
            'alias': 'testalias',
            'alert_recipients': ['test'],
            'metric': 'cpu',
            'duration': 'duration',
            'threshold': 'threashold',
            'state': 'present'
        }
        mock_find_policy.return_value = None
        mock_create.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        changed, policy = under_test._ensure_alert_policy_is_present()

        self.assertEqual(changed, True)
        self.assertEqual(policy, 'success')

    @patch.object(ClcAlertPolicy, '_create_alert_policy')
    @patch.object(clc_common, 'call_clc_api')
    def test_ensure_alert_policy_is_present_no_name(self, mock_call_api,
                                                    mock_create):
        test_params = {
            'alias': 'testalias',
            'alert_recipients': ['test'],
            'metric': 'cpu',
            'duration': 'duration',
            'threshold': 'threshold',
            'state': 'present'
        }
        mock_create.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params
        under_test.clc_auth['clc_alias'] = 'mock_alias'

        under_test._ensure_alert_policy_is_present()

        self.module.fail_json.assert_called_once_with(
            msg='Policy name is a required')

    @patch.object(ClcAlertPolicy, '_ensure_alert_policy_is_updated')
    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'call_clc_api')
    def test_ensure_alert_policy_is_present_existing(self, mock_call_api,
                                                     mock_find_policy,
                                                     mock_update):
        policy = self.policy_existing
        test_params = {
            'name': policy['name'],
            'alias': 'testalias',
            'alert_recipients': ['test'],
            'metric': 'cpu',
            'duration': 'duration',
            'threshold': 'threshold',
            'state': 'present'
        }
        mock_find_policy.return_value = policy
        mock_update.return_value = True, 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        changed, policy = under_test._ensure_alert_policy_is_present()

        self.assertEqual(changed, True)
        self.assertEqual(policy, 'success')

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'call_clc_api')
    def test_ensure_alert_policy_is_absent_name_only(self, mock_call_api,
                                                     mock_find_policy,
                                                     mock_delete):
        policy = self.policy_existing
        test_params = {
            'name': policy['name'],
            'alias': 'testalias',
            'state': 'absent'
        }
        mock_find_policy.return_value = policy
        mock_delete.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        changed, policy = under_test._ensure_alert_policy_is_absent()

        self.assertEqual(changed, True)
        self.assertEqual(policy, None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'call_clc_api')
    def test_ensure_alert_policy_is_absent_id_only(self, mock_call_api,
                                                   mock_find_policy,
                                                   mock_delete):
        policy = self.policy_existing
        test_params = {
            'id': policy['id'],
            'alias': 'testalias',
            'state': 'absent'
        }
        mock_find_policy.return_value = policy
        mock_delete.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        changed, policy = under_test._ensure_alert_policy_is_absent()

        self.assertEqual(changed, True)
        self.assertEqual(policy, None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'call_clc_api')
    def test_ensure_alert_policy_is_absent_no_id_present(self, mock_call_api,
                                                         mock_find_policy,
                                                         mock_delete):
        test_params = {
            'id': 'testid',
            'alias': 'testalias',
            'state': 'absent'
        }
        mock_find_policy.return_value = None
        mock_delete.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        changed, policy = under_test._ensure_alert_policy_is_absent()

        self.assertEqual(changed, False)
        self.assertEqual(policy, None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_delete_alert_policy')
    @patch.object(clc_common, 'find_policy')
    @patch.object(clc_common, 'call_clc_api')
    def test_ensure_alert_policy_is_absent_no_id_no_name(self, mock_call_api,
                                                         mock_find_policy,
                                                         mock_delete):
        test_params = {
            'alias': 'testalias',
            'state': 'absent'
        }
        mock_delete.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        changed, policy = under_test._ensure_alert_policy_is_absent()

        self.module.fail_json.assert_called_once_with(
            msg='Either alert policy id or policy name is required')

    @patch.object(ClcAlertPolicy, '_update_alert_policy')
    @patch.object(clc_common, 'call_clc_api')
    def test_ensure_alert_policy_is_updated_all_changed(self, mock_call_api, mock_update):
        policy = self.policy_existing
        test_params = {
            'name': policy['name'],
            'alias': 'testalias',
            'alert_recipients': ['test'],
            'metric': 'disk',
            'duration': 'duration',
            'threshold': 'threshold',
            'state': 'present'
        }
        mock_update.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        changed, policy_res = under_test._ensure_alert_policy_is_updated(policy)
        self.assertEqual(changed, True)
        self.assertEqual(policy_res, 'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_update_alert_policy')
    @patch.object(clc_common, 'call_clc_api')
    def test_ensure_alert_policy_is_updated_same_metric(self, mock_call_api, mock_update):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'disk'
            , 'duration': 'duration'
            , 'threshold': 15
            , 'state': 'absent'
        }
        mock_update.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False

        policy = {"id":"51db33be37b040f6a135abbaf989e36a","name":"alert1","actions":[{"action":"email","settings":{"recipients":["test1@centurylink.com","test2@centurylink.com"]}}],"links":[{"rel":"self","href":"/v2/alertPolicies/wfad/51db33be37b040f6a135abbaf989e36a","verbs":["GET","DELETE","PUT"]}],"triggers":[{"metric":"disk","duration":"00:05:00","threshold":5.0}]}

        under_test = ClcAlertPolicy(self.module)
        changed, policy_res = under_test._ensure_alert_policy_is_updated(policy)
        self.assertEqual(changed, True)
        self.assertEqual(policy_res,'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_update_alert_policy')
    @patch.object(clc_common, 'call_clc_api')
    def test_ensure_alert_policy_is_updated_same_met_duration(self, mock_call_api, mock_update):
        test_params = {
            'name': 'testname'
            , 'alias': 'testalias'
            , 'alert_recipients': ['test']
            , 'metric': 'disk'
            , 'duration': '00:05:00'
            , 'threshold': 15
            , 'state': 'absent'
        }
        mock_update.return_value = 'success'
        self.module.params = test_params
        self.module.check_mode = False

        policy = {"id":"51db33be37b040f6a135abbaf989e36a","name":"alert1","actions":[{"action":"email","settings":{"recipients":["test1@centurylink.com","test2@centurylink.com"]}}],"links":[{"rel":"self","href":"/v2/alertPolicies/wfad/51db33be37b040f6a135abbaf989e36a","verbs":["GET","DELETE","PUT"]}],"triggers":[{"metric":"disk","duration":"00:05:00","threshold":5.0}]}

        under_test = ClcAlertPolicy(self.module)
        changed, policy_res = under_test._ensure_alert_policy_is_updated(policy)
        self.assertEqual(changed, True)
        self.assertEqual(policy_res,'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcAlertPolicy, '_update_alert_policy')
    def test_ensure_alert_policy_is_updated_diff_recipients(self, mock_update):
        policy = self.policy_existing
        test_params = {
            'name': policy['name'],
            'alias': 'testalias',
            'alert_recipients': ['test'],
            'state': 'present'
        }
        mock_update.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        changed, policy_res = under_test._ensure_alert_policy_is_updated(policy)

        self.assertEqual(changed, True)
        self.assertEqual(policy_res, 'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_alert_policy(self, mock_call_api):
        policy = self.policy_existing
        test_params = {
            'id': policy['id'],
            'alias': 'testalias',
            'state': 'absent'
        }
        mock_call_api.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        res = under_test._delete_alert_policy(policy)

        self.assertEqual(res, 'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_alert_policy_exception(self, mock_call_api):
        policy = self.policy_existing
        test_params = {
            'id': policy['id'],
            'alias': 'testalias',
            'state': 'absent'
        }
        error = ClcApiException(message='Failed')
        mock_call_api.side_effect = error

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        under_test._delete_alert_policy(policy)

        self.module.fail_json.assert_called_once_with(
            msg='Unable to delete alert policy id: {id}. Failed'.format(
                id=policy['id']))

    @patch.object(clc_common, 'call_clc_api')
    def test_update_alert_policy(self, mock_call_api):
        policy = self.policy_existing
        test_params = {
            'name': policy['name'],
            'alias': 'testalias',
            'alert_recipients': ['test'],
            'metric': 'disk',
            'duration': '00:05:00',
            'threshold': 5,
            'state': 'present'
        }
        mock_call_api.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        res = under_test._update_alert_policy(policy)

        self.assertEqual(res, 'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_update_alert_policy_exception(self, mock_call_api):
        policy = self.policy_existing
        test_params = {
            'name': policy['name'],
            'alias': 'testalias',
            'alert_recipients': ['test'],
            'metric': 'disk',
            'duration': '00:05:00',
            'threshold': 5,
            'state': 'present'
        }
        error = ClcApiException(message='Failed')
        mock_call_api.side_effect = error

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        under_test._update_alert_policy(policy)

        self.module.fail_json.assert_called_once_with(
            msg='Unable to update alert policy: {name}. Failed'.format(
                name=policy['name']))

    @patch.object(clc_common, 'call_clc_api')
    def test_create_alert_policy(self, mock_call_api):
        test_params = {
            'name': 'testname',
            'alias': 'testalias',
            'alert_recipients': ['test'],
            'metric': 'disk',
            'duration': '00:05:00',
            'threshold': 5,
            'state': 'absent'
        }
        mock_call_api.return_value = 'success'

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        res = under_test._create_alert_policy()

        self.assertEqual(res, 'success')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_create_alert_policy_exception(self, mock_call_api):
        test_params = {
            'name': 'testname',
            'alias': 'testalias',
            'alert_recipients': ['test'],
            'metric': 'disk',
            'duration': '00:05:00',
            'threshold': 5,
            'state': 'absent'
        }
        error = ClcApiException(message='Failed')
        mock_call_api.side_effect = error

        under_test = ClcAlertPolicy(self.module)
        under_test.module.params = test_params

        under_test._create_alert_policy()

        self.module.fail_json.assert_called_once_with(
            msg='Unable to create alert policy: testname. Failed')


    def testArgumentSpecContract(self):
        args = ClcAlertPolicy._define_module_argument_spec()

        self.assertEqual(args, {'argument_spec':
                                    {'name': {'default': None},
                                     'metric': {'default': None,
                                                'choices': ['cpu', 'memory', 'disk']},
                                     'alert_recipients': {'default': None,
                                                          'type': 'list'},
                                     'alias': {'default': None, 'required': True},
                                     'state': {'default': 'present', 'choices': ['present', 'absent']},
                                     'threshold': {'default': None, 'type': 'int'},
                                     'duration': {'default': None, 'type': 'str'},
                                     'id': {'default': None}}, 'mutually_exclusive': [['name', 'id']]})


if __name__ == '__main__':
    unittest.main()
