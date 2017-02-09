#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2016 CenturyLink
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

import clc_ansible_module.clc_group_fact as clc_group_fact
from clc_ansible_module.clc_group_fact import ClcGroupFact

import clc_ansible_utils.clc as clc_common

import mock
from mock import patch
import unittest


class TestClcGroupFactFunctions(unittest.TestCase):

    def setUp(self):
        self.module = mock.MagicMock()
        self.clc_auth = {'clc_alias': 'mock_alias', 'clc_location': 'mock_dc'}

        group = mock.MagicMock()
        group.id = 'mock_id'
        group.name = 'mock_name'
        group.data = {
            'id': 'mock_id',
            'name': 'mock_name',
            'links': [
                {'rel': 'server',
                 'id': 'mock_server1'},
                {'rel': 'server',
                 'id': 'mock_server2'}
            ]
        }
        self.group = group
        self.root_group = mock.MagicMock()

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'find_group_by_id')
    def test_process_request_by_id(self, mock_find_group_id, mock_authenticate):
        mock_authenticate.return_value = self.clc_auth
        mock_find_group_id.return_value = self.group

        under_test = ClcGroupFact(self.module)
        under_test.module.params = {
            'location': 'mock_dc',
            'group_id': 'mock_id'}

        under_test.process_request()

        mock_find_group_id.assert_called_once_with(self.module, self.clc_auth,
                                                   'mock_id')
        self.module.exit_json.assert_called_once_with(changed=False,
                                                      group=self.group.data)

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'find_group')
    @patch.object(clc_common, 'group_tree')
    def test_process_request_by_name(self, mock_group_tree,
                                     mock_find_group, mock_authenticate):
        mock_authenticate.return_value = self.clc_auth
        mock_group_tree.return_value = self.root_group
        mock_find_group.return_value = self.group

        under_test = ClcGroupFact(self.module)
        under_test.module.params = {
            'location': 'mock_dc',
            'group_name': 'mock_name'}

        under_test.process_request()

        mock_find_group.assert_called_once_with(self.module, self.root_group,
                                                'mock_name')
        self.module.exit_json.assert_called_once_with(changed=False,
                                                      group=self.group.data)

    def test_process_request_no_search_key(self):
        under_test = ClcGroupFact(self.module)
        under_test.module.params = {'location': 'mock_dc'}

        under_test.process_request()

        self.module.fail_json.assert_called_once_with(
            msg='Must specify either group_id or group_name parameter.')

    def test_define_argument_spec(self):
        result = ClcGroupFact._define_module_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertTrue('argument_spec' in result)
        self.assertEqual(
            result['argument_spec'],
            dict(group_id=dict(default=None),
                 group_name=dict(default=None),
                 location=dict(default=None)))

    @patch.object(clc_group_fact, 'AnsibleModule')
    @patch.object(clc_group_fact, 'ClcGroupFact')
    def test_main(self, mock_ClcGroupFact, mock_AnsibleModule):
        mock_ClcGroupFact_instance = mock.MagicMock()
        mock_AnsibleModule_instance = mock.MagicMock()
        mock_ClcGroupFact.return_value = mock_ClcGroupFact_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_group_fact.main()

        mock_ClcGroupFact.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcGroupFact_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()
