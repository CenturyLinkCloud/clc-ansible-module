#!/usr/bin/python

import unittest

from uuid import UUID
import clc as clc_sdk
import mock
from mock import patch, create_autospec

import clc_server
from clc_server import ClcServer


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
            reload(clc_server)
            clc_server.ClcServer(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')

        # Reset clc_group
        reload(clc_server)

    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(clc_server, 'clc_sdk') as mock_clc_sdk:
                under_test = ClcServer(self.module)
                under_test._set_clc_credentials_from_env()

        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')


    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcServer(self.module)
            under_test._set_clc_credentials_from_env()

        self.assertEqual(self.module.fail_json.called, True)

    def test_define_argument_spec(self):
        result = ClcServer._define_module_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertTrue('argument_spec' in result)
        self.assertTrue('mutually_exclusive' in result)

    def test_find_running_servers_by_group(self):
        # Setup
        mock_group = create_autospec(clc_sdk.v2.Group)

        mock_running_server = mock.MagicMock()
        mock_running_server.status = 'active'
        mock_running_server.powerState = 'started'

        mock_stopped_server = mock.MagicMock()
        mock_stopped_server.status = 'active'
        mock_stopped_server.powerState = 'stopped'

        mock_group.Servers().Servers.return_value = [mock_running_server, mock_stopped_server]

        self.datacenter.Groups().Get.return_value = mock_group

        # Function Under Test
        result_servers, result_runningservers = ClcServer._find_running_servers_by_group(self.module,
                                                                                         self.datacenter,
                                                                                         "MyCoolGroup")

        # Results
        self.assertEqual(len(result_servers), 2)
        self.assertEqual(len(result_runningservers), 1)

        self.assertIn(mock_running_server, result_runningservers)
        self.assertNotIn(mock_stopped_server, result_runningservers)

        self.assertIn(mock_running_server, result_servers)
        self.assertIn(mock_stopped_server, result_servers)

        self.datacenter.reset_mock()

    def test_find_datacenter(self):
        # Setup Mocks
        def getitem(name):
            return "MyMockGroup"
        self.module.params.__getitem__.side_effect = getitem

        # Function Under Test
        ClcServer._find_datacenter(module=self.module, clc=self.clc)

        # assert result
        self.clc.v2.Datacenter.assert_called_once_with("MyMockGroup")

    def test_find_group_w_lookup_group(self):
        # Setup
        self.datacenter.Groups().Get = mock.MagicMock()

        # Function Under Test
        result_group = ClcServer._find_group(self.module, self.datacenter, "MyCoolGroup")

        # Assert Result
        self.datacenter.Groups().Get.assert_called_once_with("MyCoolGroup")
        self.assertEqual(self.module.called, False)

    def test_find_group_w_no_lookup_group(self):
        # Setup
        self.datacenter.Groups().Get = mock.MagicMock()
        self.module.params = {'group': "DefaultGroupFromModuleParamsLookup"}

        # Function Under Test
        result_group = ClcServer._find_group(self.module, self.datacenter)

        # Assert Result
        self.datacenter.Groups().Get.assert_called_once_with("DefaultGroupFromModuleParamsLookup")

    def test_find_template(self):
        self.module.params = {"template": "MyCoolTemplate"}
        self.datacenter.Templates().Search = mock.MagicMock()

        # Function Under Test
        result_template = ClcServer._find_template_id(module=self.module, datacenter=self.datacenter)

        # Assert Result
        self.datacenter.Templates().Search.assert_called_once_with("MyCoolTemplate")
        self.assertEqual(self.module.fail_json.called, False)

    def test_find_template_not_found(self):
        self.module.params = {"template": "MyCoolTemplateNotFound"}
        self.datacenter.Templates().Search = mock.MagicMock(side_effect=clc_sdk.CLCException("Template not found"))

        # Function Under Test
        result_template = ClcServer._find_template_id(module=self.module, datacenter=self.datacenter)

        # Assert Result
        self.datacenter.Templates().Search.assert_called_once_with("MyCoolTemplateNotFound")
        self.assertEqual(self.module.fail_json.called, True)

    def test_find_network_id_default(self):
        # Setup
        mock_network = mock.MagicMock()
        mock_network.name = 'TestReturnVlan'
        mock_network.id = UUID('12345678123456781234567812345678')
        self.datacenter.Networks().networks = [mock_network]
        self.module.params = {}

        # Function Under Test
        result = ClcServer._find_network_id(self.module, self.datacenter)

        # Assert Result
        self.assertEqual(result, mock_network.id)
        self.assertEqual(self.module.fail_json.called, False)

    def test_find_network_id_not_found(self):
        # Setup
        self.datacenter.Networks = mock.MagicMock(side_effect=clc_sdk.CLCException("Network not found"))
        self.module.params = {}

        # Function Under Test
        result = ClcServer._find_network_id(self.module, self.datacenter)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    def test_validate_name(self):
        # Setup
        self.module.params = {"name": "MyName"}  # Name is 6 Characters - Pass

        # Function Under Test
        ClcServer._validate_name(self.module)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, False)

    def test_validate_name_too_long(self):
        # Setup
        self.module.params = {"name": "MyNameIsTooLong"}  # Name is >6 Characters - Fail

        # Function Under Test
        result = ClcServer._validate_name(self.module)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    def test_validate_name_too_short(self):
        # Setup
        self.module.params = {"name": ""}  # Name is <1 Characters - Fail

        # Function Under Test
        result = ClcServer._validate_name(self.module)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'ClcServer')
    def test_main(self, mock_ClcServer, mock_AnsibleModule):
        mock_ClcServer_instance          = mock.MagicMock()
        mock_AnsibleModule_instance      = mock.MagicMock()
        mock_ClcServer.return_value      = mock_ClcServer_instance
        mock_AnsibleModule.return_value  = mock_AnsibleModule_instance

        clc_server.main()

        mock_ClcServer.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcServer_instance.process_request.assert_called_once

if __name__ == '__main__':
    unittest.main()
