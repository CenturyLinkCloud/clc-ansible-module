#!/usr/bin/python

import clc_ansible_module.clc_group as clc_group
from clc_ansible_module.clc_group import ClcGroup
import clc as clc_sdk
import mock
from mock import patch
import unittest

class TestClcServerFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter=mock.MagicMock()

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_group)
            clc_group.ClcGroup(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')

        # Reset clc_group
        reload(clc_group)

    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(clc_group, 'clc_sdk') as mock_clc_sdk:
                under_test = ClcGroup(self.module)
                under_test.set_clc_credentials_from_env()

        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')


    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcGroup(self.module)
            under_test.set_clc_credentials_from_env()

        self.assertEqual(self.module.fail_json.called, True)

    def test_define_argument_spec(self):
        result = ClcGroup.define_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(clc_group, 'clc_sdk')
    def test_process_request_state_present(self, mock_clc_sdk):
        self.module.params = {
            'location': 'UC1',
            'name': 'MyCoolGroup',
            'parent': 'Default Group',
            'description': 'Test Group',
            'state': 'present'
        }
        mock_group = mock.MagicMock()
        mock_group.data = {"name": "MyCoolGroup"}

        under_test = ClcGroup(self.module)
        under_test.set_clc_credentials_from_env = mock.MagicMock()
        under_test._ensure_group_is_present = mock.MagicMock(return_value=(True, mock_group))

        under_test.process_request()

        self.assertFalse(self.module.fail_json.called)
        self.module.exit_json.assert_called_once_with(changed=True, group=mock_group.data)

    @patch.object(clc_group, 'clc_sdk')
    def test_process_request_state_absent(self, mock_clc_sdk):
        self.module.params = {
            'location': 'UC1',
            'name': 'MyCoolGroup',
            'parent': 'Default Group',
            'description': 'Test Group',
            'state': 'absent'
        }
        mock_group = mock.MagicMock()
        mock_group.data = {"name": "MyCoolGroup"}

        under_test = ClcGroup(self.module)
        under_test.set_clc_credentials_from_env = mock.MagicMock()
        under_test._ensure_group_is_absent = mock.MagicMock(return_value=(True, mock_group))

        under_test.process_request()

        self.assertFalse(self.module.fail_json.called)
        self.module.exit_json.assert_called_once_with(changed=True, group=mock_group.data)

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

        under_test = ClcGroup(self.module)
        under_test.group_dict = mock_group_dict
        under_test.root_group = mock_rootgroup

        # Test
        result_changed, result_group = under_test._ensure_group_is_present(group_name=mock_group.name,
                                                                           parent_name=mock_parent.name,
                                                                           group_description="Mock Description")
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
        result_changed, result_group = under_test._ensure_group_is_present(group_name=mock_group.name,
                                                                           parent_name=mock_parent.name,
                                                                           group_description="Mock Description")
        # Assert Expected Result
        self.module.fail_json.assert_called_once_with(msg="parent group: " + mock_parent.name + " does not exist")

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
        result_changed, result_group = under_test._ensure_group_is_present(group_name=mock_group.name,
                                                                           parent_name=mock_parent.name,
                                                                           group_description="Mock Description")
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

        under_test = ClcGroup(self.module)
        under_test.group_dict = mock_group_dict

        # Test
        result_changed, result_group = under_test._ensure_group_is_absent(group_name=mock_group.name,
                                                                          parent_name=mock_parent.name)
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
        result_changed, result_group = under_test._ensure_group_is_absent(group_name=mock_group.name,
                                                                          parent_name=mock_parent.name)
        # Assert Expected Result
        self.assertEqual(result_changed, False)
        self.assertFalse(mock_group.Delete.called)

    def test_get_group(self):
        # Setup
        mock_group = mock.MagicMock(spec=clc_sdk.v2.Group)
        mock_group.name = "MyCoolGroup"

        with patch.object(clc_group, 'clc_sdk') as mock_clc_sdk:
            mock_clc_sdk.v2.Datacenter().Groups().Get.return_value = mock_group
            under_test = ClcGroup(self.module)

            # Function Under Test
            result = under_test._get_group(group_name="MyCoolGroup")

        # Assert Result
        mock_clc_sdk.v2.Datacenter().Groups().Get.assert_called_once_with("MyCoolGroup")
        self.assertEqual(result.name, "MyCoolGroup")
        self.assertEqual(self.module.fail_json.called, False)


    def test_get_group_not_found(self):

        # Setup
        with patch.object(clc_group, 'clc_sdk') as mock_clc_sdk:
            mock_clc_sdk.v2.Datacenter().Groups().Get.side_effect = clc_sdk.CLCException("Group not found")
            under_test = ClcGroup(self.module)

            # Function Under Test
            result = under_test._get_group("MyCoolGroup")

        # Assert Result
        mock_clc_sdk.v2.Datacenter().Groups().Get.assert_called_once_with("MyCoolGroup")
        self.assertEqual(result, None)
        self.assertEqual(self.module.fail_json.called, False)


    def test_get_group_exception(self):
        # Setup
        with patch.object(clc_group, 'clc_sdk') as mock_clc_sdk:
            mock_clc_sdk.v2.Datacenter().Groups().Get.side_effect = clc_sdk.CLCException("other error")
            under_test = ClcGroup(self.module)

            # Function Under Test
            result = under_test._get_group("MyCoolGroup")

        # Assert Result
        mock_clc_sdk.v2.Datacenter().Groups().Get.assert_called_once_with("MyCoolGroup")
        self.assertEqual(result, None)
        self.assertEqual(self.module.fail_json.called, True)

    @patch.object(clc_group, 'AnsibleModule')
    @patch.object(clc_group, 'ClcGroup')
    def test_main(self, mock_ClcGroup, mock_AnsibleModule):
        mock_ClcGroup_instance          = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcGroup.return_value      = mock_ClcGroup_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_group.main()

        mock_ClcGroup.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcGroup_instance.process_request.assert_called_once

if __name__ == '__main__':
    unittest.main()
