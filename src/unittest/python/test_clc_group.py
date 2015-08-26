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

import clc_ansible_module.clc_group as clc_group
from clc_ansible_module.clc_group import ClcGroup

from clc import CLCException
import clc as clc_sdk
import mock
from mock import patch
import unittest

class TestClcServerFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

    def build_mock_request_list(self, mock_server_list=None, status='succeeded'):
        mock_request_list = [mock.MagicMock()]
        for request in mock_request_list:
            reqs = []
            req1 = mock.MagicMock()
            req1.Status.return_value = status
            reqs.append(req1)
            request.requests=reqs
            request.Status.return_value = status
        return mock_request_list

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
            reload(clc_group)
            clc_group.ClcGroup(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(
            msg='clc-python-sdk required for this module')

        # Reset clc_group
        reload(clc_group)

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
            reload(clc_group)
            clc_group.ClcGroup(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library  version should be >= 2.5.0')

        # Reset clc_group
        reload(clc_group)

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
            reload(clc_group)
            clc_group.ClcGroup(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library is required for this module')

        # Reset clc_group
        reload(clc_group)

    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(clc_group, 'clc_sdk') as mock_clc_sdk:
                under_test = ClcGroup(self.module)
                under_test._set_clc_credentials_from_env()

        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(
            api_username='hansolo',
            api_passwd='falcon')

    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcGroup(self.module)
            under_test._set_clc_credentials_from_env()

        self.assertEqual(self.module.fail_json.called, True)

    def test_override_v2_api_url_from_environment(self):
        original_url = clc_sdk.defaults.ENDPOINT_URL_V2
        under_test = ClcGroup(self.module)

        under_test._set_clc_credentials_from_env()
        self.assertEqual(clc_sdk.defaults.ENDPOINT_URL_V2, original_url)

        with patch.dict('os.environ', {'CLC_V2_API_URL': 'http://unittest.example.com/'}):
            under_test._set_clc_credentials_from_env()

        self.assertEqual(
            clc_sdk.defaults.ENDPOINT_URL_V2,
            'http://unittest.example.com/')

        clc_sdk.defaults.ENDPOINT_URL_V2 = original_url

    @patch.object(clc_group, 'clc_sdk')
    def test_set_user_agent(self, mock_clc_sdk):
        clc_group.__version__ = "1"
        ClcGroup._set_user_agent(mock_clc_sdk)

        self.assertTrue(mock_clc_sdk.SetRequestsSession.called)

    @patch.object(ClcGroup, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            under_test = ClcGroup(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    def test_define_argument_spec(self):
        result = ClcGroup._define_module_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(ClcGroup, 'clc')
    def test_walk_groups_recursive(self, mock_clc_sdk):
        mock_child_group = mock.MagicMock()
        sub_group = mock.MagicMock()
        grp1 = mock.MagicMock()
        grp1.type = 'default'
        grp2 = mock.MagicMock()
        sub_group.groups = [grp1, grp2]
        mock_child_group.Subgroups.return_value = sub_group
        under_test = ClcGroup(self.module)
        res = under_test._walk_groups_recursive('parent', mock_child_group)
        self.assertIsNotNone(res)

    @patch.object(ClcGroup, '_set_clc_credentials_from_env')
    @patch.object(clc_group, 'clc_sdk')
    def test_process_request_state_present(self, mock_set_creds, mock_clc_sdk):
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
        under_test.set_clc_credentials_from_env = mock.MagicMock()
        under_test._ensure_group_is_present = mock.MagicMock(
            return_value=(
                True,
                mock_group))

        under_test.process_request()

        self.assertFalse(self.module.fail_json.called)
        self.module.exit_json.assert_called_once_with(
            changed=True,
            group=mock_group.data)

    @patch.object(ClcGroup, '_set_clc_credentials_from_env')
    @patch.object(clc_group, 'clc_sdk')
    def test_process_request_state_absent(self, mock_set_cres, mock_clc_sdk):
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
        under_test.set_clc_credentials_from_env = mock.MagicMock()
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

    def test_ensure_group_is_present_group_not_exist(self):

        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"
        mock_parent.Create.return_value = mock_group

        mock_grandparent = mock.MagicMock()
        mock_grandparent.name = "MockGrandparent"

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"

        mock_group_dict = {mock_parent.name: (mock_parent, mock_grandparent)}

        self.module.check_mode = False
        under_test = ClcGroup(self.module)
        under_test.group_dict = mock_group_dict
        under_test.root_group = mock_rootgroup

        # Test
        result_changed, result_group = under_test._ensure_group_is_present(
            group_name=mock_group.name, parent_name=mock_parent.name, group_description="Mock Description")
        # Assert Expected Result
        self.assertTrue(result_changed)
        self.assertEqual(result_group, mock_group)
        self.assertFalse(self.module.fail_json.called)

    def test_ensure_group_is_present_parent_not_exist(self):

        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"

        mock_group_dict = {}

        under_test = ClcGroup(self.module)
        under_test.group_dict = mock_group_dict
        under_test.root_group = mock_rootgroup

        # Test
        result_changed, result_group = under_test._ensure_group_is_present(
            group_name=mock_group.name, parent_name=mock_parent.name, group_description="Mock Description")
        # Assert Expected Result
        self.module.fail_json.assert_called_once_with(
            msg="parent group: " +
            mock_parent.name +
            " does not exist")

    def test_ensure_group_is_present_parent_and_group_exist(self):

        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"
        mock_parent.Create.return_value = mock_group

        mock_grandparent = mock.MagicMock()
        mock_grandparent.name = "MockGrandparent"

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"

        mock_group_dict = {mock_parent.name: (mock_parent, mock_grandparent),
                           mock_group.name: (mock_group, mock_parent)}

        under_test = ClcGroup(self.module)
        under_test.group_dict = mock_group_dict
        under_test.root_group = mock_rootgroup

        # Test
        result_changed, result_group = under_test._ensure_group_is_present(
            group_name=mock_group.name, parent_name=mock_parent.name, group_description="Mock Description")
        # Assert Expected Result
        self.assertFalse(result_changed)
        self.assertEqual(result_group, mock_group)
        self.assertFalse(self.module.fail_json.called)

    def test_ensure_group_is_absent_group_exists(self):

        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"

        mock_group_dict = {mock_group.name: (mock_group, mock_parent)}

        self.module.check_mode = False
        under_test = ClcGroup(self.module)
        under_test.group_dict = mock_group_dict

        # Test
        result_changed, result_group, result = under_test._ensure_group_is_absent(
            group_name=mock_group.name, parent_name=mock_parent.name)
        # Assert Expected Result
        self.assertEqual(result_changed, True)
        mock_group.Delete.assert_called_once()

    def test_ensure_group_is_absent_group_not_exists(self):

        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"

        mock_group_dict = {}

        under_test = ClcGroup(self.module)
        under_test.group_dict = mock_group_dict

        # Test
        result_changed, result_group, response = under_test._ensure_group_is_absent(
            group_name=mock_group.name, parent_name=mock_parent.name)
        # Assert Expected Result
        self.assertEqual(result_changed, False)
        self.assertFalse(mock_group.Delete.called)

    def test_create_group_exception(self):
        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "MockGroup"

        error = CLCException('Failed')
        error.response_text = 'group failed'

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"
        mock_parent.Create.side_effect = error

        mock_grandparent = mock.MagicMock()
        mock_grandparent.name = "MockGrandparent"

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"

        mock_group_dict = {mock_parent.name: (mock_parent, mock_grandparent),
                           mock_group.name: (mock_group, mock_parent)}

        under_test = ClcGroup(self.module)
        under_test.group_dict = mock_group_dict
        under_test.root_group = mock_rootgroup
        ret = under_test._create_group('test', mock_parent.name, 'test')
        self.assertIsNone(ret, 'The return value should be None')
        self.module.fail_json.assert_called_once_with(msg='Failed to create group :test. group failed')

    def test_delete_group_exception(self):
        # Setup Test
        mock_group = mock.MagicMock()
        mock_group.name = "test"

        error = CLCException('Failed')
        error.response_text = 'group failed'
        mock_group.Delete.side_effect = error

        mock_parent = mock.MagicMock()
        mock_parent.name = "MockParent"

        mock_grandparent = mock.MagicMock()
        mock_grandparent.name = "MockGrandparent"

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = "MockRootGroup"

        mock_group_dict = {mock_parent.name: (mock_parent, mock_grandparent),
                           mock_group.name: (mock_group, mock_parent)}

        under_test = ClcGroup(self.module)
        under_test.group_dict = mock_group_dict
        under_test.root_group = mock_rootgroup
        ret = under_test._delete_group('test')
        self.assertIsNone(ret, 'The return value should be None')
        self.module.fail_json.assert_called_once_with(msg='Failed to delete group :test. group failed')

    def test_wait_for_requests_to_complete_req_successful(self):
        mock_request_list = self.build_mock_request_list(status='succeeded')
        under_test = ClcGroup(self.module)._wait_for_requests_to_complete
        under_test(mock_request_list)
        self.assertFalse(self.module.fail_json.called)

    def test_wait_for_requests_to_complete_req_failed(self):
        mock_request_list = self.build_mock_request_list(status='failed')
        under_test = ClcGroup(self.module)._wait_for_requests_to_complete
        under_test(mock_request_list)
        self.module.fail_json.assert_called_once_with(msg='Unable to process group request')

    def test_wait_for_requests_to_complete_no_wait(self):
        mock_request_list = self.build_mock_request_list(status='failed')
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
        mock_ClcGroup_instance.process_request.assert_called_once

if __name__ == '__main__':
    unittest.main()
