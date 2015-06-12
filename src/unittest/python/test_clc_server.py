#!/usr/bin/python

import unittest

from uuid import UUID
import clc as clc_sdk
from clc import CLCException
from clc import APIFailedResponse
import mock
from mock import patch, create_autospec

import clc_ansible_module.clc_server as clc_server
from clc_ansible_module.clc_server import ClcServer


class TestClcServerFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

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

    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_state_absent(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Test
        self.module.params = {
            'state': 'absent',
            'server_ids': ['TEST_SERVER'],
            'location': 'UC1',
            'type': 'standard',
            'storage_type': 'standard',
            'wait': True
        }

        mock_server = mock.MagicMock()
        mock_request = mock.MagicMock()
        mock_server.id = 'TEST_SERVER'
        mock_server.Delete.return_value = mock_request

        mock_clc_sdk.v2.Servers().Servers.return_value = [mock_server]

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(changed=True, servers=[], server_ids=['TEST_SERVER'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_exact_count_1_server_w_pubip(self,
                                                          mock_clc_sdk,
                                                          mock_set_clc_creds):
        # Setup Fixture
        self.module.params = {
            'state': 'present',
            'name': 'TEST',
            'location': 'UC1',
            'type': 'standard',
            'template': 'TEST_TEMPLATE',
            'storage_type': 'standard',
            'wait': True,
            'exact_count': 1,
            'count_group': 'Default Group',
            'add_public_ip': True,
            'public_ip_protocol': 'TCP',
            'public_ip_ports': [80]
        }

        # Define Mock Objects
        mock_server = mock.MagicMock()
        mock_requests = mock.MagicMock()
        mock_single_request = mock.MagicMock()
        mock_group = mock.MagicMock()
        mock_template = mock.MagicMock()
        mock_network = mock.MagicMock()

        # Set Mock Server Return Values
        mock_server.id = 'TEST_SERVER'
        mock_server.data = {'name': 'TEST_SERVER'}
        mock_server.details = {'ipAddresses': [{'internal': '1.2.3.4'}]}
        mock_server.PublicIPs().public_ips = ['5.6.7.8']

        # Set Mock Request Return Values
        mock_single_request.Server.return_value = mock_server
        mock_requests.WaitUntilComplete.return_value = 0
        mock_requests.requests = [mock_single_request]

        # Set Mock Template / Network Values
        mock_template.id = 'TEST_TEMPLATE'
        mock_network.id = '12345'

        # Set Mock Group Values
        mock_group.Defaults.return_value = 1
        mock_group.id = '12345'

        # Setup Mock API Responses
        def _api_call_return_values(*args, **kwargs):
            if kwargs.get('method') == 'GET':
                return {'id': '12345'}
            if kwargs.get('method') == 'POST':
                return {'links': [{'rel': 'self', 'id': '12345'}]}

        mock_clc_sdk.v2.API.Call.side_effect = _api_call_return_values
        mock_clc_sdk.v2.Datacenter().Groups().Get.return_value = mock_group
        mock_clc_sdk.v2.Group.return_value = mock_group
        mock_clc_sdk.v2.Server.return_value = mock_server
        mock_clc_sdk.v2.Account.GetAlias.return_value = 'TST'
        mock_clc_sdk.v2.Datacenter().Templates().Search().__getitem__.return_value = mock_template
        mock_clc_sdk.v2.Datacenter().Networks().networks.__getitem__.return_value = mock_network
        mock_clc_sdk.v2.Requests.return_value = mock_requests
        mock_clc_sdk.v2.API.Call.side_effect = _api_call_return_values

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        # Assert
        mock_server.PublicIPs().Add.assert_called_with([{'protocol': 'TCP', 'port': 80}])
        self.module.exit_json.assert_called_once_with(changed=True,
                                                      servers=[{'publicip': '5.6.7.8',
                                                                'ipaddress': '1.2.3.4',
                                                                'name': 'TEST_SERVER'}],
                                                      server_ids=['TEST_SERVER'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_exact_count_delete_1_server(self,
                                                         mock_clc_sdk,
                                                         mock_set_clc_creds):
        # Setup Fixture
        self.module.params = {
            'state': 'present',
            'name': 'TEST',
            'location': 'UC1',
            'type': 'standard',
            'template': 'TEST_TEMPLATE',
            'storage_type': 'standard',
            'wait': True,
            'exact_count': 0,
            'count_group': 'Default Group',
        }

        # Define Mock Objects
        mock_server = mock.MagicMock()
        mock_group = mock.MagicMock()

        # Set Mock Server Return Values
        mock_server.id = 'TEST_SERVER'
        mock_server.status = 'active'
        mock_server.powerState = 'started'

        # Set Mock Group Values
        mock_group.Servers().Servers.return_value = [mock_server]

        # Setup Mock API Calls
        mock_clc_sdk.v2.Servers().Servers.return_value = [mock_server]
        mock_clc_sdk.v2.Datacenter().Groups().Get.return_value = mock_group

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(changed=True,
                                                      servers=[],
                                                      server_ids=['TEST_SERVER'])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_start_server(self,
                                          mock_clc_sdk,
                                          mock_set_clc_creds):
        # Setup Fixture
        self.module.params = {
            'state': 'started',
            'server_ids': ['UC1TESTSVR01'],
            'wait': True
        }

        # Define Mock Objects
        mock_server = mock.MagicMock()
        mock_request = mock.MagicMock()

        # Set Mock Server Return Values
        mock_server.id = 'TEST_SERVER'
        mock_server.data = {'name': 'TEST_SERVER'}
        mock_server.powerState = 'stopped'
        mock_server.PowerOn.return_value = mock_request

        mock_request.WaitUntilComplete.return_value = 0

        mock_clc_sdk.v2.Servers().Servers.return_value = [mock_server]

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(server_ids=['TEST_SERVER'],
                                                      changed=True,
                                                      servers=[{'name': 'TEST_SERVER'}])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_server, 'clc_sdk')
    def test_find_server_by_uuid_404_response(self,
                                              mock_clc_sdk):
        # Define Mock Objects
        mock_server = mock.MagicMock()

        # Set Mock Server Return Values
        mock_server.id = 'TEST_SERVER'
        mock_server.data = {'name': 'TEST_SERVER'}
        mock_server.details = {'ipAddresses': [{'internal': '1.2.3.4'}]}

        num_api_errors_to_generate = [1]

        # Setup Mock API Responses
        def _api_call_return_values(*args, **kwargs):
            if num_api_errors_to_generate[0] > 0:
                num_api_errors_to_generate[0] -= 1
                error = APIFailedResponse()
                error.response_status_code = 404
                raise error
            else:
                return {'id': '12345'}

        mock_clc_sdk.v2.API.Call.side_effect = _api_call_return_values
        mock_clc_sdk.v2.Server.return_value  = mock_server

        # Test
        under_test = ClcServer(self.module)
        result = under_test._find_server_by_uuid_w_retry(clc=mock_clc_sdk,
                                                         module=self.module,
                                                         svr_uuid='12345',
                                                         alias='TST',
                                                         retries=2)

        # Assert
        self.assertEqual(result, mock_server)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_server, 'clc_sdk')
    def test_find_server_by_uuid_too_many_404_responses(self,
                                                        mock_clc_sdk):
        # Define Mock Objects
        mock_server = mock.MagicMock()

        # Set Mock Server Return Values
        mock_server.id = 'TEST_SERVER'
        mock_server.data = {'name': 'TEST_SERVER'}
        mock_server.details = {'ipAddresses': [{'internal': '1.2.3.4'}]}

        num_api_errors_to_generate = [2]

        # Setup Mock API Responses
        def _api_call_return_values(*args, **kwargs):
            if num_api_errors_to_generate[0] > 0:
                num_api_errors_to_generate[0] -= 1
                error = APIFailedResponse()
                error.response_status_code = 404
                raise error
            else:
                return {'id': '12345'}

        mock_clc_sdk.v2.API.Call.side_effect = _api_call_return_values
        mock_clc_sdk.v2.Server.return_value  = mock_server

        # Test
        under_test = ClcServer(self.module)
        result = under_test._find_server_by_uuid_w_retry(clc=mock_clc_sdk,
                                                         module=self.module,
                                                         svr_uuid='12345',
                                                         alias='TST',
                                                         retries=1)

        # Assert
        self.module.fail_json.assert_called_with(msg='Unable to reach the CLC API after 5 attempts')

    @patch.object(clc_server, 'clc_sdk')
    def test_find_server_by_uuid_other_api_error_response(self,
                                                          mock_clc_sdk):
        # Define Mock Objects
        mock_server = mock.MagicMock()

        # Set Mock Server Return Values
        mock_server.id = 'TEST_SERVER'
        mock_server.data = {'name': 'TEST_SERVER'}
        mock_server.details = {'ipAddresses': [{'internal': '1.2.3.4'}]}
        api_error = APIFailedResponse()
        api_error.response_status_code = 500
        api_error.message = "ERROR_MESSAGE"

        mock_clc_sdk.v2.API.Call.side_effect = api_error
        mock_clc_sdk.v2.Server.return_value  = mock_server

        # Test
        under_test = ClcServer(self.module)
        result = under_test._find_server_by_uuid_w_retry(clc=mock_clc_sdk,
                                                         module=self.module,
                                                         svr_uuid='12345',
                                                         alias='TST')

        # Assert
        self.module.fail_json.assert_called_with(msg='A failure response was received from CLC API when'
                                                     ' attempting to get details for a server:  '
                                                     'UUID=12345, Code=500, Message=ERROR_MESSAGE')

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

    def test_override_v2_api_url_from_environment(self):
        original_url = clc_sdk.defaults.ENDPOINT_URL_V2
        under_test = ClcServer(self.module)

        under_test._set_clc_credentials_from_env()
        self.assertEqual(clc_sdk.defaults.ENDPOINT_URL_V2, original_url)

        with patch.dict('os.environ', {'CLC_V2_API_URL': 'http://unittest.example.com/'}):
            under_test._set_clc_credentials_from_env()

        self.assertEqual(clc_sdk.defaults.ENDPOINT_URL_V2, 'http://unittest.example.com/')

        clc_sdk.defaults.ENDPOINT_URL_V2 = original_url

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
        # Setup Test
        self.module.params = {
            'location': "MyMockGroup"
        }

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

    @patch.object(clc_server, 'clc_sdk')
    def test_find_group_w_recursive_lookup(self,
                                           mock_clc_sdk):
        # Setup
        mock_datacenter = mock.MagicMock()
        mock_group_to_find = mock.MagicMock()
        mock_group = mock.MagicMock()
        mock_subgroup = mock.MagicMock()
        mock_subsubgroup = mock.MagicMock()

        mock_group_to_find.name = "TEST_RECURSIVE_GRP"

        mock_datacenter.Groups().Get.side_effect = CLCException()
        mock_datacenter.Groups().groups = [mock_group]

        mock_group.Subgroups().Get.side_effect = CLCException()
        mock_group.Subgroups().groups = [mock_subgroup]

        mock_subgroup.Subgroups().Get.side_effect = CLCException()
        mock_subgroup.Subgroups().groups = [mock_subsubgroup]

        mock_subsubgroup.Subgroups().Get.return_value = mock_group_to_find

        # Test
        under_test = ClcServer(self.module)
        result = under_test._find_group(module=self.module,
                                        datacenter=mock_datacenter,
                                        lookup_group="TEST_RECURSIVE_GRP")
        # Assert
        self.assertEqual(mock_group_to_find, result)

    def test_find_template(self):
        self.module.params = {"template": "MyCoolTemplate", "state": "present"}
        self.datacenter.Templates().Search = mock.MagicMock()

        # Function Under Test
        result_template = ClcServer._find_template_id(module=self.module, datacenter=self.datacenter)

        # Assert Result
        self.datacenter.Templates().Search.assert_called_once_with("MyCoolTemplate")
        self.assertEqual(self.module.fail_json.called, False)

    def test_find_template_not_found(self):
        self.module.params = {"template": "MyCoolTemplateNotFound", "state": "present"}
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
        self.module.params = {"name": "MyName", "state": "present"}  # Name is 6 Characters - Pass

        # Function Under Test
        ClcServer._validate_name(self.module)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, False)

    def test_validate_name_too_long(self):
        # Setup
        self.module.params = {"name": "MyNameIsTooLong", "state": "present"}  # Name is >6 Characters - Fail

        # Function Under Test
        result = ClcServer._validate_name(self.module)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    def test_validate_name_too_short(self):
        # Setup
        self.module.params = {"name": "", "state": "present"}  # Name is <1 Characters - Fail

        # Function Under Test
        result = ClcServer._validate_name(self.module)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    @patch.object(clc_server, 'clc_sdk')
    def test_get_anti_affinity_policy_id_singe_match(self, mock_clc_sdk):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'}]}]

        policy_id = ClcServer._get_anti_affinity_policy_id(mock_clc_sdk, None, 'alias', 'test1')
        self.assertEqual('111', policy_id)

    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'clc_sdk')
    def test_get_anti_affinity_policy_id_no_match(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'}]}]

        policy_id = ClcServer._get_anti_affinity_policy_id(mock_clc_sdk, mock_ansible_module, 'alias', 'testnone')
        mock_ansible_module.fail_json.assert_called_with(
            msg='No anti affinity policy was found with policy name : testnone')

    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'clc_sdk')
    def test_get_anti_affinity_policy_id_duplicate_match(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'},
                                                 {'name' : 'test1', 'id' : '111'}]}]

        policy_id = ClcServer._get_anti_affinity_policy_id(mock_clc_sdk, mock_ansible_module, 'alias', 'test1')
        mock_ansible_module.fail_json.assert_called_with(
            msg='mutiple anti affinity policies were found with policy name : test1')


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
