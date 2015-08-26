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
            ClcServer(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')

        # Reset
        reload(clc_server)

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
            reload(clc_server)
            ClcServer(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library  version should be >= 2.5.0')

        # Reset
        reload(clc_server)

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
            reload(clc_server)
            ClcServer(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library is required for this module')

        # Reset
        reload(clc_server)

    @patch.object(clc_server, 'clc_sdk')
    def test_set_user_agent(self, mock_clc_sdk):
        clc_server.__version__ = "1"
        ClcServer._set_user_agent(mock_clc_sdk)

        self.assertTrue(mock_clc_sdk.SetRequestsSession.called)

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
        self.module.exit_json.assert_called_once_with(changed=True,
                                                      servers=[],
                                                      server_ids=['TEST_SERVER'],
                                                      partially_created_server_ids=[])
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
            'wait': False,
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

        self.module.check_mode = False

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        # Assert
        mock_server.PublicIPs().Add.assert_called_with([{'protocol': 'TCP', 'port': 80}])
        self.module.exit_json.assert_called_once_with(changed=True,
                                                      servers=[{'publicip': '5.6.7.8',
                                                                'ipaddress': '1.2.3.4',
                                                                'name': 'TEST_SERVER'}],
                                                      server_ids=['TEST_SERVER'],
                                                      partially_created_server_ids=[])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_exact_count_1_server_w_no_alert_pol_name(self,
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
            'add_public_ip': False,
            'public_ip_protocol': 'TCP',
            'public_ip_ports': [80],
            'alert_policy_name': 'test alert policy'
        }
        self.module.check_mode = False

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
                return {'id': '12345','name': 'test alert policy'}
            if kwargs.get('method') == 'POST':
                return {'links': [{'rel': 'self', 'id': '12345'}]}

        mock_clc_sdk.v2.Datacenter().Groups().Get.return_value = mock_group
        mock_clc_sdk.v2.Group.return_value = mock_group
        mock_clc_sdk.v2.Server.return_value = mock_server
        mock_clc_sdk.v2.Account.GetAlias.return_value = 'TST'
        mock_clc_sdk.v2.Datacenter().Templates().Search().__getitem__.return_value = mock_template
        mock_clc_sdk.v2.Datacenter().Networks().networks.__getitem__.return_value = mock_network
        mock_clc_sdk.v2.Requests.return_value = mock_requests
        mock_clc_sdk.v2.API.Call.side_effect = _api_call_return_values

        self.module.check_mode = False

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        # Assert
        self.assertTrue(self.module.fail_json.called)
        self.module.fail_json.assert_called_with(msg='No alert policy exist with name : test alert policy')

    @patch.object(ClcServer, '_get_alert_policy_id_by_name')
    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_count_1_server_w_alert_pol_name(self,
                                                          mock_clc_sdk,
                                                          mock_set_clc_creds,
                                                          mock_get_alert_policy):
        # Setup Fixture
        self.module.params = {
            'state': 'present',
            'name': 'TEST',
            'location': 'UC1',
            'type': 'standard',
            'template': 'TEST_TEMPLATE',
            'storage_type': 'standard',
            'wait': True,
            'count': 1,
            'count_group': 'Default Group',
            'add_public_ip': False,
            'public_ip_protocol': 'TCP',
            'public_ip_ports': [80],
            'alert_policy_name': 'test alert policy'
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
                return {'id': '12345','name': 'test alert policy'}
            if kwargs.get('method') == 'POST':
                return {'links': [{'rel': 'self', 'id': '12345'}]}

        mock_clc_sdk.v2.Datacenter().Groups().Get.return_value = mock_group
        mock_clc_sdk.v2.Group.return_value = mock_group
        mock_clc_sdk.v2.Server.return_value = mock_server
        mock_clc_sdk.v2.Account.GetAlias.return_value = 'TST'
        mock_clc_sdk.v2.Datacenter().Templates().Search().__getitem__.return_value = mock_template
        mock_clc_sdk.v2.Datacenter().Networks().networks.__getitem__.return_value = mock_network
        mock_clc_sdk.v2.Requests.return_value = mock_requests
        mock_clc_sdk.v2.API.Call.side_effect = _api_call_return_values
        mock_get_alert_policy.return_value = '12345'

        self.module.check_mode = False

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        #Assert
        #self.assertFalse(self.module.fail_json.called)
        self.assertTrue(self.module.exit_json.called)
        self.module.exit_json.assert_called_once_with(changed=True,
                                                      servers=[{'ipaddress': '1.2.3.4',
                                                                'name': 'TEST_SERVER'}],
                                                      server_ids=['TEST_SERVER'],
                                                      partially_created_server_ids=[])


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
                                                      server_ids=['TEST_SERVER'],
                                                      partially_created_server_ids=[])
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
        mock_server.PublicIPs().public_ips.__getitem__.return_value = "5.6.7.8"
        mock_server.details['ipAddresses'][0].__getitem__.return_value = "1.2.3.4"

        mock_request.WaitUntilComplete.return_value = 0

        mock_clc_sdk.v2.Servers().Servers.return_value = [mock_server]

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(server_ids=['TEST_SERVER'],
                                                      changed=True,
                                                      servers=[{'name': 'TEST_SERVER',
                                                                'publicip': '5.6.7.8',
                                                                'ipaddress': '1.2.3.4'}],
                                                      partially_created_server_ids=[])
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
        mock_clc_sdk.v2.Account.GetAlias.return_value  = 'TST'

        # Test
        under_test = ClcServer(self.module)
        result = under_test._find_server_by_uuid_w_retry(clc=mock_clc_sdk,
                                                         module=self.module,
                                                         svr_uuid='12345',
                                                         alias=None,
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

    def test_set_clc_credentials_w_token(self):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'Token12345',
                                       'CLC_ACCT_ALIAS': 'TEST' }):
            mock_clc_sdk = mock.MagicMock()
            under_test = ClcServer(self.module)
            under_test.clc = mock_clc_sdk
            under_test._set_clc_credentials_from_env()
            self.assertEqual(mock_clc_sdk._LOGIN_TOKEN_V2, 'Token12345')
            self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
            self.assertEqual(self.module.fail_json.called, False)

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
    def test_find_aa_policy_id_no_match(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'}]}]

        params = {
            'alias': 'test',
            'anti_affinity_policy_id': None,
            'anti_affinity_policy_name': 'nothing'
        }
        mock_ansible_module.params = params
        ClcServer._find_aa_policy_id(mock_clc_sdk, mock_ansible_module)
        mock_ansible_module.fail_json.assert_called_with(
            msg='No anti affinity policy was found with policy name : nothing')

    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'clc_sdk')
    def test_get_anti_affinity_policy_id_duplicate_match(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'},
                                                 {'name' : 'test1', 'id' : '111'}]}]

        policy_id = ClcServer._get_anti_affinity_policy_id(mock_clc_sdk, mock_ansible_module, 'alias', 'test1')
        mock_ansible_module.fail_json.assert_called_with(
            msg='multiple anti affinity policies were found with policy name : test1')

    @patch.object(clc_server, 'clc_sdk')
    def test_get_anti_affinity_policy_id_get_fail(self, mock_clc_sdk):
        error = APIFailedResponse()
        error.response_text = 'Mock failure message'
        mock_clc_sdk.v2.API.Call.side_effect = error
        under_test = ClcServer(self.module)
        under_test._get_anti_affinity_policy_id(mock_clc_sdk, self.module, 'alias', 'aa_policy_name')
        self.module.fail_json.assert_called_with(msg='Unable to fetch anti affinity policies for account: alias. Mock failure message')

    @patch.object(clc_server, 'clc_sdk')
    def test_create_clc_server_exception(self, mock_clc_sdk):
        error = APIFailedResponse()
        error.response_text = 'Mock failure message'
        mock_clc_sdk.v2.API.Call.side_effect = error
        under_test = ClcServer(self.module)
        server_params = {
            'alias': 'mock',
            'name': 'test server'
        }
        under_test._create_clc_server(mock_clc_sdk, self.module, server_params)
        self.module.fail_json.assert_called_with(msg='Unable to create the server: test server. Mock failure message')

    @patch.object(clc_server, 'clc_sdk')
    def test_find_datacenter_exception(self, mock_clc_sdk):
        error = CLCException()
        mock_clc_sdk.v2.Datacenter.side_effect = error
        params = {
            'state': 'present',
            'location': 'testdc'
        }
        self.module.params = params
        under_test = ClcServer(self.module)
        under_test._find_datacenter(mock_clc_sdk, self.module)
        self.module.fail_json.assert_called_with(msg='Unable to find location: testdc')

    @patch.object(ClcServer, '_find_group_recursive')
    def test_find_group_no_result(self, mock_find_recursive):
        mock_find_recursive.return_value = None
        mock_dc = mock.MagicMock()
        mock_dc.id = 'testdc'
        mock_dc.Groups().Get.side_effect = CLCException()
        under_test = ClcServer(self.module)
        ret = under_test._find_group(self.module, mock_dc, 'lookup_group')
        self.module.fail_json.assert_called_with(msg='Unable to find group: lookup_group in location: testdc')
        self.assertEqual(ret, None)

    @patch.object(clc_server, 'clc_sdk')
    def test_find_cpu_exception(self, mock_clc_sdk):
        params = {
            'state': 'present'
        }
        mock_group = mock.MagicMock()
        mock_group.Defaults.return_value = None
        mock_clc_sdk.v2.Group.return_value = mock_group
        self.module.params = params
        ClcServer._find_cpu(mock_clc_sdk, self.module)
        self.module.fail_json.assert_called_with(msg="Can't determine a default cpu value. Please provide a value for cpu.")

    @patch.object(clc_server, 'clc_sdk')
    def test_find_memory_exception(self, mock_clc_sdk):
        params = {
            'state': 'present'
        }
        mock_group = mock.MagicMock()
        mock_group.Defaults.return_value = None
        mock_clc_sdk.v2.Group.return_value = mock_group
        self.module.params = params
        ClcServer._find_memory(mock_clc_sdk, self.module)
        self.module.fail_json.assert_called_with(msg="Can't determine a default memory value. Please provide a value for memory.")

    def test_validate_types_exception_standard(self):
        params = {
            'state': 'present',
            'type': 'standard',
            'storage_type': 'invalid'
        }
        self.module.params = params
        ClcServer._validate_types(self.module)
        self.module.fail_json.assert_called_with(msg="Standard VMs must have storage_type = 'standard' or 'premium'")

    def test_validate_types_exception_hyperscale(self):
        params = {
            'state': 'present',
            'type': 'hyperscale',
            'storage_type': 'invalid'
        }
        self.module.params = params
        ClcServer._validate_types(self.module)
        self.module.fail_json.assert_called_with(msg="Hyperscale VMs must have storage_type = 'hyperscale'")

    @patch.object(clc_server, 'clc_sdk')
    def test_find_ttl(self, mock_clc_sdk):
        params = {
            'state': 'present',
            'ttl': 5000
        }
        self.module.params = params
        mock_clc_sdk.v2.time_utils.SecondsToZuluTS.return_value = 'TTL'
        res = ClcServer._find_ttl(mock_clc_sdk, self.module)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(res, 'TTL')

    @patch.object(clc_server, 'clc_sdk')
    def test_find_ttl_exception(self, mock_clc_sdk):
        params = {
            'state': 'present',
            'ttl': 1000
        }
        self.module.params = params
        mock_clc_sdk.v2.time_utils.SecondsToZuluTS.return_value = 'TTL'
        ClcServer._find_ttl(mock_clc_sdk, self.module)
        self.module.fail_json.assert_called_with(msg='Ttl cannot be <= 3600')

    def test_startstop_servers_invalid_list(self):
        ClcServer._start_stop_servers(self.module, self.clc, {'id': 'value'})
        self.module.fail_json.assert_called_with(msg='server_ids should be a list of servers, aborting')

    def test_delete_servers_invalid_list(self):
        ClcServer._delete_servers(self.module, self.clc, {'id': 'value'})
        self.module.fail_json.assert_called_with(msg='server_ids should be a list of servers, aborting')

    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(ClcServer, '_validate_module_params')
    def test_process_request_absent_state_w_invalid_servers(self, mock_validate, mock_creds):
        params = {
            'state': 'absent',
            'server_ids': {'data': 'invalid'}
        }
        mock_validate.return_value = params
        under_test = ClcServer(self.module)
        under_test.process_request()
        self.module.fail_json.assert_called_with(msg="server_ids needs to be a list of instances to delete: {'data': 'invalid'}")

    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(ClcServer, '_validate_module_params')
    def test_process_request_started_state_w_invalid_servers(self, mock_validate, mock_creds):
        params = {
            'state': 'started',
            'server_ids': {'data': 'invalid'}
        }
        mock_validate.return_value = params
        under_test = ClcServer(self.module)
        under_test.process_request()
        self.module.fail_json.assert_called_with(msg="server_ids needs to be a list of servers to run: {'data': 'invalid'}")

    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(ClcServer, '_validate_module_params')
    def test_process_request_present_state_w_no_template(self, mock_validate, mock_creds):
        params = {
            'state': 'present',
            'server_ids': ['id1', 'id2']
        }
        mock_validate.return_value = params
        under_test = ClcServer(self.module)
        under_test.process_request()
        self.module.fail_json.assert_called_with(msg='template parameter is required for new instance')

    @patch.object(clc_server, 'clc_sdk')
    def test_add_alert_policy_to_server_exception(self, mock_clc_sdk):
        error = APIFailedResponse()
        error.response_text = 'Mock failure message'
        mock_clc_sdk.v2.API.Call.side_effect = error
        under_test = ClcServer(self.module)
        server_params = {
            'alias': 'mock',
            'name': 'test server'
        }
        self.assertRaises(CLCException,
                          under_test._add_alert_policy_to_server,
                          mock_clc_sdk,
                          'alias',
                          'server_id',
                          'alert_policy_id')

    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'clc_sdk')
    def test_get_alert_policy_id_by_name_dup_match(self, mock_clc_sdk, mock_ansible_module):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'},
                                                 {'name' : 'test1', 'id' : '111'}]}]

        ClcServer._get_alert_policy_id_by_name(mock_clc_sdk, mock_ansible_module, 'alias', 'test1')
        mock_ansible_module.fail_json.assert_called_with(
            msg='multiple alert policies were found with policy name : test1')

    @patch.object(clc_server, 'clc_sdk')
    def test_get_alert_policy_id_by_name(self, mock_clc_sdk):
        mock_clc_sdk.v2.API.Call.side_effect = [{'items' :
                                                [{'name' : 'test1', 'id' : '111'},
                                                 {'name' : 'test2', 'id' : '222'}]}]

        policy_id = ClcServer._get_alert_policy_id_by_name(mock_clc_sdk, None, 'alias', 'test1')
        self.assertEqual('111', policy_id)

    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'clc_sdk')
    def test_change_server_power_state_started(self, mock_clc_sdk, mock_ansible_module):
        server = mock.MagicMock()
        server.PowerOn.return_value = 'OK'
        result = ClcServer._change_server_power_state(mock_ansible_module, server, 'started')
        self.assertEqual(result, 'OK')
        self.assertEqual(mock_ansible_module.fail_json.called, False)

    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'clc_sdk')
    def test_change_server_power_state_stopped(self, mock_clc_sdk, mock_ansible_module):
        server = mock.MagicMock()
        server.PowerOff.return_value = 'OK'
        result = ClcServer._change_server_power_state(mock_ansible_module, server, 'stopped')
        self.assertEqual(result, 'OK')
        self.assertEqual(mock_ansible_module.fail_json.called, False)

    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'clc_sdk')
    def test_change_server_power_state_error(self, mock_clc_sdk, mock_ansible_module):
        error = CLCException('Failed')
        server = mock.MagicMock()
        server.id = 'server1'
        server.PowerOff.side_effect = error
        result = ClcServer._change_server_power_state(mock_ansible_module, server, 'stopped')
        self.assertEqual(result, None)
        mock_ansible_module.fail_json.assert_called_with(msg='Unable to change power state for server server1')

    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'clc_sdk')
    def test_add_alert_policy_to_servers(self, mock_clc_sdk, mock_ansible_module):
        params = {
            'alias': 'test',
            'alert_policy_id': '123',
        }
        mock_ansible_module.params = params
        mock_ansible_module.check_mode = False
        server = mock.MagicMock()
        server.id = 'server1'
        servers = [server]
        result = ClcServer._add_alert_policy_to_servers(mock_clc_sdk, mock_ansible_module, servers)
        self.assertEqual(result, [])
        self.assertFalse(mock_ansible_module.fail_json.called)

    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'clc_sdk')
    def test_add_alert_policy_to_servers_error(self, mock_clc_sdk, mock_ansible_module):
        error = CLCException('Failed')
        mock_clc_sdk.v2.API.Call.side_effect = error
        params = {
            'alias': 'test',
            'alert_policy_id': '123',
        }
        mock_ansible_module.params = params
        mock_ansible_module.check_mode = False
        server = mock.MagicMock()
        server.id = 'server1'
        servers = [server]
        result = ClcServer._add_alert_policy_to_servers(mock_clc_sdk, mock_ansible_module, servers)
        self.assertEqual(result[0].id, 'server1')

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

    @patch.object(ClcServer, '_wait_for_requests')
    @patch.object(ClcServer, '_create_clc_server')
    @patch.object(ClcServer, '_add_alert_policy_to_servers')
    @patch.object(ClcServer, '_add_public_ip_to_servers')
    @patch.object(clc_server, 'AnsibleModule')
    @patch.object(clc_server, 'clc_sdk')
    def test_create_servers_w_partial_servers(self, mock_clc_sdk, mock_ansible_module,
                                              mock_public_ip, mock_alert_pol, mock_create_server,
                                              mock_wait_for_requests):
        mock_ansible_module.check_mode = False
        mock_alert_pol.return_value = ['server2']
        mock_wait_for_requests.return_value = 'success'
        mock_request = mock.MagicMock()
        mock_server = mock.MagicMock()
        mock_server.id = 'server1'
        mock_request.requests[0].Server.side_effect = [mock_server]
        mock_public_ip.return_value = [mock_server]
        mock_create_server.return_value = mock_request
        under_test = ClcServer(mock_ansible_module)
        server_dict_array, created_server_ids, partial_created_servers_ids, changed = \
            under_test._create_servers(mock_ansible_module, mock_clc_sdk)
        self.assertEqual(changed, True)
        self.assertEqual(partial_created_servers_ids, ['server1'])

    def test_create_servers_no_change(self):
        params = {
            'state': 'present',
            'count': 0
        }
        self.module.params = params
        under_test = ClcServer(self.module)
        server_dict_array, created_server_ids, partial_created_servers_ids, changed = \
            under_test._create_servers(self.module, self.clc)
        self.assertEqual(changed, False)
        self.assertEqual(server_dict_array, [])
        self.assertEqual(created_server_ids, [])
        self.assertEqual(partial_created_servers_ids, [])

    def test_enforce_count_missing_argument(self):
        params = {
            'state': 'present',
            'exact_count': 1
        }
        self.module.params = params
        under_test = ClcServer(self.module)
        under_test._enforce_count(self.module, self.clc)
        self.module.fail_json.assert_called_with(msg="you must use the 'count_group' option with exact_count")

    @patch.object(ClcServer, '_find_running_servers_by_group')
    def test_enforce_count_no_change(self, mock_running_servers):
        mock_server_list = [mock.MagicMock()]
        mock_running_servers.return_value = (mock_server_list, mock_server_list)
        params = {
            'state': 'present',
            'exact_count': 0,
            'count_group': 'test'
        }
        self.module.params = params
        under_test = ClcServer(self.module)
        server_dict_array, changed_server_ids, partial_servers_ids, changed = \
            under_test._enforce_count(self.module, self.clc)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(changed, False)
        self.assertEqual(server_dict_array, [])
        self.assertEqual(changed_server_ids, [])
        self.assertEqual(partial_servers_ids, [])

    def test_add_public_ip_to_servers_w_failed_servers(self):
        mock_server = mock.MagicMock()
        mock_server.id = 'server1'
        mock_server.PublicIPs().Add.side_effect = APIFailedResponse()
        servers = [mock_server]
        self.module.check_mode = False
        under_test = ClcServer(self.module)
        failed_servers = under_test._add_public_ip_to_servers(
                                             self.module,
                                             True, servers,
                                             'TCP',
                                             [80])
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(len(failed_servers), 1)
        self.assertEqual(failed_servers[0].id, 'server1')

    @patch.object(clc_server, 'clc_sdk')
    def test_delete_servers(self, mock_clc_sdk):
        params = {
            'wait': False
        }
        self.module.params = params
        mock_server = mock.MagicMock()
        mock_server.id = 'mockid1'
        mock_servers = mock.MagicMock()
        mock_servers.id = 'temp1'
        mock_servers.Servers.return_value = [mock_server]
        mock_clc_sdk.v2.Servers.return_value = mock_servers
        self.module.check_mode = False
        under_test = ClcServer(self.module)
        changed, server_dict_array, terminated_server_ids = \
            under_test._delete_servers(self.module, mock_clc_sdk, ['server1', 'server2'])
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(changed, True)
        self.assertEqual(terminated_server_ids, ['mockid1'])

    @patch.object(clc_server, 'clc_sdk')
    def test_start_stop_servers(self, mock_clc_sdk):
        params = {
            'wait': False
        }
        self.module.params = params
        mock_server = mock.MagicMock()
        mock_server.id = 'mockid1'
        mock_servers = mock.MagicMock()
        mock_servers.id = 'temp1'
        mock_servers.Servers.return_value = [mock_server]
        mock_clc_sdk.v2.Servers.return_value = mock_servers
        self.module.check_mode = False
        under_test = ClcServer(self.module)
        changed, server_dict_array, result_server_ids = \
            under_test._start_stop_servers(self.module, mock_clc_sdk, ['server1', 'server2'])
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(changed, True)
        self.assertEqual(result_server_ids, ['mockid1'])

    def test_wait_for_requests_fail(self):
        under_test = ClcServer(self.module)
        mock_request = mock.MagicMock()
        mock_request.WaitUntilComplete.return_value = 1
        under_test._wait_for_requests(self.module, [mock_request])
        self.module.fail_json.assert_called_with(msg='Unable to process server request')

    def test_refresh_servers_fail(self):
        error = CLCException()
        error.message = 'Mock fail message'
        under_test = ClcServer(self.module)
        mock_server = mock.MagicMock()
        mock_server.id = 'mock_server_id'
        mock_server.Refresh.side_effect = error
        mock_servers = [mock_server]
        under_test._refresh_servers(self.module, mock_servers)
        self.module.fail_json.assert_called_with(msg='Unable to refresh the server mock_server_id. Mock fail message')

    @patch.object(clc_server, 'clc_sdk')
    def test_find_alias_exception(self, mock_clc_sdk):
        error = CLCException()
        error.message = 'Mock fail message'
        mock_clc_sdk.v2.Account.GetAlias.side_effect = error
        self.module.params = {}
        under_test = ClcServer(self.module)
        under_test._find_alias(mock_clc_sdk, self.module)
        self.module.fail_json.assert_called_with(msg='Unable to find account alias. Mock fail message')


if __name__ == '__main__':
    unittest.main()
