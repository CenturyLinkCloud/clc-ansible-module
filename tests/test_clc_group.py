#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

import clc_ansible_module.clc_group as clc_group
from clc_ansible_module.clc_group import ClcGroup

import urllib2
import mock
from mock import patch
import unittest

class TestClcGroupFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

    def build_mock_request_list(self, status_code=200):
        mock_request_list = []
        req1 = mock.MagicMock()
        req1.code = status_code
        mock_request_list.append(req1)
        return mock_request_list

    def test_define_argument_spec(self):
        result = ClcGroup._define_module_argument_spec()
        self.assertIsInstance(result, dict)

    def test_walk_groups_recursive(self):
        group_data = {'name': 'Mock Group', 'id': 'mock_id',
                      'type': 'mock_type', 'groups': []}
        grp1 = mock.MagicMock()
        grp1.type = 'default'
        grp1.children = []
        under_test = ClcGroup(self.module)
        res = under_test._walk_groups_recursive(grp1, group_data)
        self.assertIsNotNone(res)

    @patch.object(ClcGroup, '_get_group_tree_for_datacenter')
    def test_process_request_state_present(self, mock_group_tree):
        self.module.params = {
            'location': 'UC1',
            'name': 'MyCoolGroup',
            'parent': 'Default Group',
            'description': 'Test Group',
            'state': 'present',
            'wait': 'True'
        }
        mock_group = mock.MagicMock()
        mock_group.data = {"name": "MyCoolGroup"}

        under_test = ClcGroup(self.module)
        under_test.api._set_clc_credentials_from_env = mock.MagicMock()
        under_test._ensure_group_is_present = mock.MagicMock(
            return_value=(
                True,
                mock_group))

        under_test.process_request()

        self.assertFalse(self.module.fail_json.called)
        self.module.exit_json.assert_called_once_with(
            changed=True,
            group=mock_group.data)

    @patch.object(ClcGroup, '_get_group_tree_for_datacenter')
    def test_process_request_state_absent(self, mock_group_tree):
        self.module.params = {
            'location': 'UC1',
            'name': 'MyCoolGroup',
            'parent': 'Default Group',
            'description': 'Test Group',
            'state': 'absent',
            'wait': 'True'
        }
        mock_group = mock.MagicMock()
        mock_group = {"name": "MyCoolGroup"}
        mock_response = mock.MagicMock()

        under_test = ClcGroup(self.module)
        under_test.api._set_clc_credentials_from_env = mock.MagicMock()
        under_test._ensure_group_is_absent = mock.MagicMock(
            return_value=(
                True,
                mock_group,
                mock_response))

        under_test.process_request()

        self.assertFalse(self.module.fail_json.called)
        self.module.exit_json.assert_called_once_with(
            changed=True,
            group='MyCoolGroup')

    @patch.object(ClcGroup, '_create_group')
    def test_ensure_group_is_present_group_not_exist(self, mock_create_group):

        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"
        mock_parent.children = []
        mock_parent.Create.return_value = mock_group

        mock_grandparent = mock.MagicMock()
        mock_grandparent.name = "MockGrandparent"
        mock_grandparent.children = [mock_parent]
        mock_parent.parent = mock_grandparent

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"
        mock_rootgroup.parent = None
        mock_rootgroup.children = [mock_grandparent]
        mock_grandparent.parent = mock_rootgroup

        self.module.check_mode = False
        under_test = ClcGroup(self.module)
        under_test.root_group = mock_rootgroup
        under_test._create_group.return_value = mock_group

        # Test
        result_changed, result_group = under_test._ensure_group_is_present(
            group_name=mock_group.name, parent_name=mock_parent.name, group_description="Mock Description")
        # Assert Expected Result
        self.assertTrue(result_changed)
        self.assertEqual(result_group, mock_group)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcGroup, '_create_group')
    def test_ensure_group_is_present_parent_not_exist(self, mock_create_group):

        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"
        mock_rootgroup.parent = None
        mock_rootgroup.children = []


        under_test = ClcGroup(self.module)
        under_test.root_group = mock_rootgroup

        # Test
        result_changed, result_group = under_test._ensure_group_is_present(
            group_name=mock_group.name, parent_name=mock_parent.name, group_description="Mock Description")
        # Assert Expected Result
        self.assertFalse(under_test._create_group.called)
        self.module.fail_json.assert_called_once_with(
            msg="parent group: " +
            mock_parent.name +
            " does not exist")

    @patch.object(ClcGroup, '_create_group')
    def test_ensure_group_is_present_parent_and_group_exist(self,
                                                            mock_create_group):

        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"
        mock_parent.children = [mock_group]
        mock_group.parent = mock_parent

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"
        mock_rootgroup.parent = None
        mock_rootgroup.children = [mock_parent]
        mock_parent.parent = mock_rootgroup

        under_test = ClcGroup(self.module)
        under_test.root_group = mock_rootgroup
        under_test._create_group.return_value = mock_group

        # Test
        result_changed, result_group = under_test._ensure_group_is_present(
            group_name=mock_group.name, parent_name=mock_parent.name, group_description="Mock Description")
        # Assert Expected Result
        self.assertFalse(result_changed)
        self.assertEqual(result_group, mock_group)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcGroup, '_delete_group')
    def test_ensure_group_is_absent_group_exists(self, mock_delete_group):

        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"
        mock_parent.children = [mock_group]
        mock_group.parent = mock_parent

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = 'MockRootGroup'
        mock_rootgroup.parent = None
        mock_rootgroup.children = [mock_parent]
        mock_parent.parent = mock_rootgroup

        self.module.check_mode = False
        under_test = ClcGroup(self.module)
        under_test.root_group = mock_rootgroup

        # Test
        result_changed, result_group, result = under_test._ensure_group_is_absent(
            group_name=mock_group.name, parent_name=mock_parent.name)
        # Assert Expected Result
        self.assertEqual(result_changed, True)
        self.assertTrue(under_test._delete_group.called)

    @patch.object(ClcGroup, '_delete_group')
    def test_ensure_group_is_absent_group_not_exists(self, mock_delete_group):

        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"
        mock_parent.children = []

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = 'MockRootGroup'
        mock_rootgroup.parent = None
        mock_rootgroup.children = [mock_parent]
        mock_parent.parent = mock_rootgroup

        under_test = ClcGroup(self.module)
        under_test.root_group = mock_rootgroup

        # Test
        result_changed, result_group, response = under_test._ensure_group_is_absent(
            group_name=mock_group.name, parent_name=mock_parent.name)
        # Assert Expected Result
        self.assertEqual(result_changed, False)
        self.assertFalse(under_test._delete_group.called)

    def test_create_group_exception(self):
        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"
        mock_parent.children = [mock_group]
        mock_group.parent = mock_parent

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"
        mock_rootgroup.children = [mock_parent]
        mock_parent.parent = mock_rootgroup

        under_test = ClcGroup(self.module)
        under_test.root_group = mock_rootgroup

        fp = mock.MagicMock()
        error = urllib2.HTTPError('http://unittest.com', 404, 'NOT FOUND',
                                  {}, fp)
        under_test.api = mock.MagicMock()
        under_test.api.call.side_effect = error

        ret = under_test._create_group('test', mock_parent.name, 'test')
        self.assertIsNone(ret, 'The return value should be None')
        self.module.fail_json.assert_called_once_with(
            msg='Failed to create group :test. {0}'.format(error))

    def test_delete_group_exception(self):
        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "test"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"
        mock_parent.children = [mock_group]
        mock_group.parent = mock_parent

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"
        mock_rootgroup.children = [mock_parent]
        mock_parent.parent = mock_rootgroup

        under_test = ClcGroup(self.module)
        under_test.root_group = mock_rootgroup

        fp = mock.MagicMock()
        error = urllib2.HTTPError('http://unittest.com', 404, 'NOT FOUND',
                                  {}, fp)
        under_test.api = mock.MagicMock()
        under_test.api.call.side_effect = error

        ret = under_test._delete_group('test', mock_parent.name)
        self.assertIsNone(ret, 'The return value should be None')
        self.module.fail_json.assert_called_once_with(
            msg='Failed to delete group :test. {0}'.format(error))

    def test_wait_for_requests_to_complete_req_successful(self):
        mock_request_list = self.build_mock_request_list(status_code=200)
        under_test = ClcGroup(self.module)._wait_for_requests_to_complete
        under_test(mock_request_list)
        self.assertFalse(self.module.fail_json.called)

    def test_wait_for_requests_to_complete_req_failed(self):
        mock_request_list = self.build_mock_request_list(status_code=404)
        under_test = ClcGroup(self.module)._wait_for_requests_to_complete
        under_test(mock_request_list)
        self.module.fail_json.assert_called_once_with(msg='Unable to process group request')

    def test_wait_for_requests_to_complete_no_wait(self):
        mock_request_list = self.build_mock_request_list(status_code=404)
        params = {
            'wait': False
        }
        self.module.params = params
        under_test = ClcGroup(self.module)._wait_for_requests_to_complete
        under_test(mock_request_list)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_group, 'AnsibleModule')
    @patch.object(clc_group, 'ClcGroup')
    def test_main(self, mock_ClcGroup, mock_AnsibleModule):
        mock_ClcGroup_instance = mock.MagicMock()
        mock_AnsibleModule_instance = mock.MagicMock()
        mock_ClcGroup.return_value = mock_ClcGroup_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_group.main()

        mock_ClcGroup.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcGroup_instance.process_request.call_count == 1

if __name__ == '__main__':
    unittest.main()
