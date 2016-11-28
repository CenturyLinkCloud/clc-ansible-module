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

import unittest
import requests
from uuid import UUID
import os
import clc as clc_sdk
from clc import CLCException
from clc import APIFailedResponse
import mock
from mock import patch, create_autospec

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import clc_ansible_module.clc_server as clc_server
from clc_ansible_module.clc_server import ClcServer


class TestClcServerFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()
        self.server = ClcServer(self.module)
        self.server.clc_common = mock.MagicMock()

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        real_import = __import__
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

    @patch.object(clc_server, 'clc_common')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_state_absent(self, mock_clc_sdk, mock_clc_common):
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

        # Set Mock Group Return values
        mock_existing_server = mock.MagicMock()
        mock_existing_server.id = "EXISTING_SERVER"
        mock_result_group = mock.MagicMock()
        mock_result_group.data = { "id":"1111111" }
        mock_result_group.Servers().Servers.return_value = [ mock_existing_server ]

        # Set Mock Group Values
        mock_group = mock.MagicMock()
        mock_group.Defaults.return_value = 1
        mock_group.id = '12345'

        mock_clc_sdk.v2.Datacenter().Groups().Get.side_effect = [ mock_group, mock_result_group ]

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(changed=True,
                                                      group={ "id": "1111111", "servers": [ "EXISTING_SERVER" ]},
                                                      servers=[],
                                                      server_ids=['TEST_SERVER'],
                                                      partially_created_server_ids=[])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_server, 'clc_common')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_exact_count_1_server_w_pubip(self, mock_clc_sdk,
                                                          mock_clc_common):
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
                                                      group=None,
                                                      servers=[{'publicip': '5.6.7.8',
                                                                'ipaddress': '1.2.3.4',
                                                                'name': 'TEST_SERVER'}],
                                                      server_ids=['TEST_SERVER'],
                                                      partially_created_server_ids=[])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_server, 'clc_common')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_exact_count_1_server_w_no_alert_pol_name(
            self, mock_clc_sdk, mock_clc_common):
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

    @patch.object(clc_server, 'clc_common')
    @patch.object(ClcServer, '_get_alert_policy_id_by_name')
    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_count_1_server_w_alert_pol_name(
            self, mock_clc_sdk, mock_get_alert_policy, mock_clc_common):
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

        # Set Mock Group Return values
        mock_existing_server = mock.MagicMock()
        mock_existing_server.id = "EXISTING_SERVER"
        mock_result_group = mock.MagicMock()
        mock_result_group.data = { "id":"1111111" }
        mock_result_group.Servers().Servers.return_value = [ mock_existing_server, mock_server ]

        # Setup Mock API Responses
        def _api_call_return_values(*args, **kwargs):
            if kwargs.get('method') == 'GET':
                return {'id': '12345','name': 'test alert policy'}
            if kwargs.get('method') == 'POST':
                return {'links': [{'rel': 'self', 'id': '12345'}] }

        mock_clc_sdk.v2.Datacenter().Groups().Get.side_effect = [ mock_group, mock_result_group ]
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
                                                      group={ "id": "1111111", "servers": [ "EXISTING_SERVER", "TEST_SERVER" ]},
                                                      servers=[{'ipaddress': '1.2.3.4',
                                                                'name': 'TEST_SERVER'}],
                                                      server_ids=['TEST_SERVER'],
                                                      partially_created_server_ids=[])
    
    @patch.object(clc_server, 'clc_common')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_count_1_bare_metal_server(self, mock_clc_sdk,
                                                       mock_clc_common):
        # Setup Fixture
        self.module.params = {
            'state': 'present',
            'name': 'TEST',
            'location': 'UC1',
            'type': 'bareMetal',
            'wait': True,
            'count': 1,
            'count_group': 'Default Group',
            'configuration_id': 'test bare metal config',
            'os_type': 'ubuntu14_64Bit'
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

        # Set Mock Group Return values
        mock_existing_server = mock.MagicMock()
        mock_existing_server.id = "EXISTING_SERVER"
        mock_result_group = mock.MagicMock()
        mock_result_group.data = { "id":"1111111" }
        mock_result_group.Servers().Servers.return_value = [ mock_existing_server, mock_server ]

        # Setup Mock API Responses
        def _api_call_return_values(*args, **kwargs):
            if kwargs.get('method') == 'GET':
                return {'id': '12345','name': 'test'}
            if kwargs.get('method') == 'POST':
                return {'links': [{'rel': 'self', 'id': '12345'}]}

        mock_clc_sdk.v2.Datacenter().Groups().Get.side_effect = [ mock_group, mock_result_group ]
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

        #Assert
        #self.assertFalse(self.module.fail_json.called)
        self.assertTrue(self.module.exit_json.called)
        self.module.exit_json.assert_called_once_with(changed=True,
                                                      group={ "id": "1111111", "servers": [ "EXISTING_SERVER", "TEST_SERVER" ]},
                                                      servers=[{'ipaddress': '1.2.3.4',
                                                                'name': 'TEST_SERVER'}],
                                                      server_ids=['TEST_SERVER'],
                                                      partially_created_server_ids=[])

    @patch.object(clc_server, 'clc_common')
    @patch.object(ClcServer, '_enforce_count')
    @patch.object(ClcServer, '_set_clc_credentials_from_env')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_exact_count_delete_1_server(self,
                                                         mock_clc_sdk,
                                                         mock_enforce_count,
                                                         mock_clc_common):
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

        # Set Mock Server Return Values
        mock_server.id = 'TEST_SERVER'
        mock_server.status = 'active'
        mock_server.powerState = 'started'

        # Set Mock Group Return values
        mock_existing_server = mock.MagicMock()
        mock_existing_server.id = "EXISTING_SERVER"
        mock_result_group = mock.MagicMock()
        mock_result_group.data = { "id":"1111111" }
        mock_result_group.Servers().Servers.return_value = [ mock_existing_server, mock_server ]

        mock_clc_sdk.v2.Datacenter().Groups().Get.return_value = mock_result_group
        mock_enforce_count.return_value = ([], [mock_server.id], [], True)

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(changed=True,
                                                      group={ "id": "1111111", "servers": [ "EXISTING_SERVER", "TEST_SERVER" ]},
                                                      servers=[],
                                                      server_ids=['TEST_SERVER'],
                                                      partially_created_server_ids=[])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_server, 'clc_common')
    @patch.object(clc_server, 'clc_sdk')
    def test_process_request_start_server(self, mock_clc_sdk, mock_clc_common):
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

        # Set Mock Group Values
        mock_group = mock.MagicMock()
        mock_group.Defaults.return_value = 1
        mock_group.id = '12345'

        # Set Mock Group Return values
        mock_existing_server = mock.MagicMock()
        mock_existing_server.id = "EXISTING_SERVER"
        mock_result_group = mock.MagicMock()
        mock_result_group.data = { "id":"1111111" }
        mock_result_group.Servers().Servers.return_value = [ mock_existing_server, mock_server ]

        mock_request.WaitUntilComplete.return_value = 0

        mock_clc_sdk.v2.Datacenter().Groups().Get.side_effect = [ mock_group, mock_result_group ]
        mock_clc_sdk.v2.Servers().Servers.return_value = [mock_server]

        # Test
        under_test = ClcServer(self.module)
        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(server_ids=['TEST_SERVER'],
                                                      group={ "id": "1111111", "servers": [ "EXISTING_SERVER", "TEST_SERVER" ]},
                                                      changed=True,
                                                      servers=[{'name': 'TEST_SERVER',
                                                                'publicip': '5.6.7.8',
                                                                'ipaddress': '1.2.3.4'}],
                                                      partially_created_server_ids=[])
        self.assertFalse(self.module.fail_json.called)


    @patch.object(clc_common, 'Server')
    @patch.object(clc_common, 'call_clc_api')
    def test_find_server_by_uuid_404_response(self, mock_call_api,
                                              mock_clc_server):
        # Define Mock Objects
        mock_server = mock.MagicMock()

        # Set Mock Server Return Values
        mock_server.id = 'TEST_ID'
        mock_server.name = 'TEST_NAME'
        mock_server.data = {
            'id': 'TEST_ID',
            'name': 'TEST_NAME',
            'details': {'ipAddresses': [{'internal': '1.2.3.4'}]},
        }

        num_api_errors_to_generate = [1]

        # Setup Mock API Responses
        def _api_call_return_values(*args, **kwargs):
            if num_api_errors_to_generate[0] > 0:
                num_api_errors_to_generate[0] -= 1
                error = ClcApiException(message='ERROR_MESSAGE', code=404)
                error.code = 404
                raise error
            else:
                return mock_server.data

        mock_call_api.side_effect = _api_call_return_values
        mock_clc_server.return_value = mock_server

        # Test
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        result = under_test._find_server_by_uuid_w_retry(
            svr_uuid='12345', alias=None, retries=2, back_out=0)

        # Assert
        self.assertEqual(result, mock_server)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_find_server_by_uuid_too_many_404_responses(self, mock_call_api):
        # Define Mock Objects
        mock_server = mock.MagicMock()

        # Set Mock Server Return Values
        mock_server.id = 'TEST_ID'
        mock_server.name = 'TEST_NAME'
        mock_server.data = {
            'id': 'TEST_ID',
            'name': 'TEST_NAME',
            'details': {'ipAddresses': [{'internal': '1.2.3.4'}]},
        }

        num_api_errors_to_generate = [2]

        # Setup Mock API Responses
        def _api_call_return_values(*args, **kwargs):
            if num_api_errors_to_generate[0] > 0:
                num_api_errors_to_generate[0] -= 1
                error = ClcApiException(message='ERROR_MESSAGE', code=404)
                raise error
            else:
                return mock_server.data

        mock_call_api.side_effect = _api_call_return_values

        # Test
        under_test = ClcServer(self.module)
        result = under_test._find_server_by_uuid_w_retry(
            svr_uuid='12345', alias='TST', retries=2, back_out=0)

        # Assert
        self.module.fail_json.assert_called_with(
            msg='Unable to reach the CLC API after 2 attempts')

    @patch.object(clc_common, 'call_clc_api')
    def test_find_server_by_uuid_other_api_error_response(self, mock_call_api):
        # Define Mock Objects
        mock_server = mock.MagicMock()

        # Set Mock Server Return Values
        # Set Mock Server Return Values
        mock_server.id = 'TEST_ID'
        mock_server.name = 'TEST_NAME'
        mock_server.data = {
            'id': 'TEST_ID',
            'name': 'TEST_NAME',
            'details': {'ipAddresses': [{'internal': '1.2.3.4'}]},
        }
        api_error = ClcApiException(message='ERROR_MESSAGE', code=500)

        mock_call_api.side_effect = api_error

        # Test
        under_test = ClcServer(self.module)
        result = under_test._find_server_by_uuid_w_retry(
            svr_uuid='12345', alias='TST', back_out=0)

        # Assert
        self.module.fail_json.assert_called_with(
            msg='A failure response was received from CLC API when'
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

    @patch.object(ClcServer, '_find_group')
    @patch.object(clc_common, 'servers_in_group')
    def test_find_running_servers_by_group(self, mock_servers, mock_find_group):
        # Setup
        mock_running_server = mock.MagicMock()
        mock_running_server.status = 'active'
        mock_running_server.powerState = 'started'

        mock_stopped_server = mock.MagicMock()
        mock_stopped_server.status = 'active'
        mock_stopped_server.powerState = 'stopped'

        mock_servers.return_value = [mock_running_server, mock_stopped_server]

        # Function Under Test
        under_test = ClcServer(self.module)
        result_servers, result_runningservers = under_test._find_running_servers_by_group(
            'dummy_group',
            "MyCoolGroup")

        # Results
        self.assertEqual(len(result_servers), 2)
        self.assertEqual(len(result_runningservers), 1)

        self.assertIn(mock_running_server, result_runningservers)
        self.assertNotIn(mock_stopped_server, result_runningservers)

        self.assertIn(mock_running_server, result_servers)
        self.assertIn(mock_stopped_server, result_servers)

        self.datacenter.reset_mock()

    @patch.object(clc_common, 'authenticate')
    def test_find_datacenter(self, mock_authenticate):
        # Setup Test
        self.module.params = {
            'location': "MyMockGroup"
        }

        # Function Under Test
        under_test = ClcServer(self.module)
        under_test._find_datacenter()

        mock_authenticate.assert_called_once()
        self.assertTrue(under_test.clc_auth['clc_location'], 'MyMockGroup')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'find_group')
    @patch.object(clc_common, 'group_tree')
    def test_find_group_w_lookup_group(self, mock_group_tree, mock_find_group):
        # Setup
        mock_rootgroup = mock.MagicMock()
        clc_common.group_tree.return_value = mock_rootgroup

        # Function Under Test
        under_test = ClcServer(self.module)
        under_test.root_group = mock_rootgroup
        result_group = under_test._find_group(self.datacenter, "MyCoolGroup")

        # Assert Result
        clc_common.find_group.assert_called_once_with(
            self.module, mock_rootgroup,
            'MyCoolGroup')
        self.assertEqual(self.module.fail_json.called, False)


    @patch.object(clc_common, 'find_group')
    @patch.object(clc_common, 'group_tree')
    def test_find_group_w_no_lookup_group(self, mock_group_tree,
                                          mock_find_group):
        # Setup
        mock_rootgroup = mock.MagicMock()
        self.module.params = {'group': "DefaultGroupFromModuleParamsLookup"}
        clc_common.group_tree.return_value = mock_rootgroup

        # Function Under Test
        under_test = ClcServer(self.module)
        result_group = under_test._find_group(self.datacenter)

        # Assert Result
        clc_common.find_group.assert_called_once_with(
            self.module, mock_rootgroup,
            'DefaultGroupFromModuleParamsLookup')

    def test_find_group_w_recursive_lookup(self):
        # Setup
        mock_group_to_find = mock.MagicMock()
        mock_group_to_find.name = "TEST_RECURSIVE_GRP"

        mock_rootgroup = mock.MagicMock()
        mock_rootgroup.name = 'rootgroup'
        mock_rootgroup.parent = None

        mock_subgroup = mock.MagicMock()
        mock_subgroup.name = 'subgroup'
        mock_rootgroup.children = [mock_subgroup]
        mock_subgroup.parent = mock_rootgroup

        mock_subsubgroup = mock.MagicMock()
        mock_subsubgroup.name = 'subsubgroup'
        mock_subgroup.children = [mock_subsubgroup]
        mock_subsubgroup.parent = mock_subgroup

        mock_subsubgroup.children = [mock_group_to_find]
        mock_group_to_find.parent = mock_subsubgroup

        # Test
        under_test = ClcServer(self.module)
        under_test.root_group = mock_rootgroup
        result = under_test._find_group('datacenter',
                                        lookup_group="TEST_RECURSIVE_GRP")
        # Assert
        self.assertEqual(mock_group_to_find, result)

    @patch.object(clc_common, 'call_clc_api')
    def test_find_template(self, mock_call_api):
        # Function Under Test
        under_test = ClcServer(self.module)
        under_test.module.params = {"template": "MyCoolTemplate",
                                    "state": "present"}
        datacenter = 'mock_datacenter'
        clc_auth = {'clc_alias': 'mock_alias'}
        under_test.clc_auth = clc_auth
        result_template = under_test._find_template_id(datacenter)

        # Assert Result
        mock_call_api.assert_called_once_with(
            under_test.module, under_test.clc_auth, 'GET',
            '/datacenters/mock_alias/mock_datacenter/deploymentCapabilities')
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(clc_common, 'call_clc_api')
    def test_find_template_not_found(self, mock_call_api):
        # Function Under Test
        under_test = ClcServer(self.module)
        under_test.module.params = {"template": "MyCoolTemplateNotFound",
                                    "state": "present"}
        clc_auth = {'clc_alias': 'mock_alias'}
        datacenter = 'mock_datacenter'
        under_test.clc_auth = clc_auth
        result_template = under_test._find_template_id(datacenter)

        # Assert Result
        mock_call_api.assert_called_once_with(
            under_test.module, under_test.clc_auth, 'GET',
            '/datacenters/mock_alias/mock_datacenter/deploymentCapabilities')
        self.assertIsNone(result_template)

    @patch.object(clc_common, 'call_clc_api')
    def test_find_network_id_default(self, mock_call_api):
        # Setup
        mock_network = mock.MagicMock()
        mock_network['name'] = 'TestReturnVlan'
        mock_network['id'] = '12345678123456781234567812345678'
        datacenter = 'mock_dc'

        mock_call_api.return_value = [mock_network]
        self.module.params = {}

        # Function Under Test
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        result = under_test._find_network_id(datacenter)

        # Assert Result
        self.assertEqual(result, mock_network['id'])
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(clc_common, 'call_clc_api')
    def test_find_network_id_by_id(self, mock_call_api):
        # Setup
        mock_network = mock.MagicMock()
        mock_network['name'] = 'TestReturnVlan'
        mock_network['id'] = '12345678123456781234567812345678'
        datacenter = 'mock_dc'

        mock_call_api.return_value = [mock_network]
        self.module.params = {'network_id': mock_network['id']}

        # Function Under Test
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        result = under_test._find_network_id(datacenter)

        # Assert Result
        self.assertEqual(result, mock_network['id'])
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(clc_common, 'call_clc_api')
    def test_find_network_id_invalid_id(self, mock_call_api):
        # Setup
        mock_network = mock.MagicMock()
        mock_network['name'] = 'TestReturnVlan'
        mock_network['id'] = '12345678123456781234567812345678'
        datacenter = 'mock_dc'

        mock_call_api.return_value = [mock_network]
        self.module.params = {'network_id': 'mock_network_id'}

        # Function Under Test
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        result = under_test._find_network_id(datacenter)

        # Assert Result
        self.module.fail_json.assert_called_once_with(
            msg='No matching network: mock_network_id '
                'found in location: mock_dc')

    @patch.object(clc_common, 'call_clc_api')
    def test_find_network_id_not_found(self, mock_call_api):
        # Setup
        datacenter = 'mock_dc'
        mock_call_api.side_effect = ClcApiException()
        self.module.params = {}

        # Function Under Test
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        result = under_test._find_network_id(datacenter)

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    def test_validate_name(self):
        # Setup
        self.module.params = {"name": "MyName", "state": "present"}  # Name is <=6 Characters - Pass

        # Function Under Test
        ClcServer._validate_name(self.module, 'aa')

        # Assert Result
        self.assertEqual(self.module.fail_json.called, False)

    def test_validate_name_too_long(self):
        # Setup
        self.module.params = {"name": "MyNameIsTooLong", "state": "present"}  # Name is >6 Characters - Fail

        # Function Under Test
        result = ClcServer._validate_name(self.module, 'hi')

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    def test_validate_name_too_short(self):
        # Setup
        self.module.params = {"name": "", "state": "present"}  # Name is <1 Characters - Fail

        # Function Under Test
        result = ClcServer._validate_name(self.module, 'n/a')

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    def test_validate_name_acct_alias_2_server_name_8(self):
        # Setup
        self.module.params = {"name": "12345678", "state": "present"}  # AA = 2 chars; name = 8 chars -> pass

        # Function Under Test
        result = ClcServer._validate_name(self.module, "AB")

        # Assert Result
        self.assertEqual(self.module.fail_json.called, False)

    def test_validate_name_acct_alias_3_server_name_7(self):
        # Setup
        self.module.params = {"name": "1234567", "state": "present"}  # AA = 3 chars; name = 7 chars -> pass

        # Function Under Test
        result = ClcServer._validate_name(self.module, "ABC")

        # Assert Result
        self.assertEqual(self.module.fail_json.called, False)

    def test_validate_name_acct_alias_6_server_name_5(self):
        # Setup
        self.module.params = {"name": "12345", "state": "present"}  # AA = 6 chars; name = 5 chars -> fail

        # Function Under Test
        result = ClcServer._validate_name(self.module, "ABCDEF")

        # Assert Result
        self.assertEqual(self.module.fail_json.called, True)

    @patch.object(clc_common, 'call_clc_api')
    def test_find_aa_policy_id_singe_match(self, mock_call_api):
        mock_call_api.return_value = {
            'items': [{'name': 'test1', 'id': '111'},
                      {'name': 'test2', 'id': '222'}]}

        under_test = ClcServer(self.module)
        under_test.clc_auth = {'clc_alias': 'mock_alias'}
        under_test.module.params = {'anti_affinity_policy_name': 'test1'}
        self.assertEqual('111', under_test._find_aa_policy_id())

    @patch.object(clc_common, 'call_clc_api')
    def test_find_aa_policy_id_no_match(self, mock_call_api):
        mock_call_api.return_value = {
            'items': [{'name': 'test1', 'id': '111'},
                      {'name': 'test2', 'id': '222'}]}

        params = {
            'alias': 'test',
            'anti_affinity_policy_id': None,
            'anti_affinity_policy_name': 'nothing'
        }
        under_test = ClcServer(self.module)
        under_test.clc_auth = {'clc_alias': 'mock_alias'}
        under_test.module.params = params
        under_test._find_aa_policy_id()
        under_test.module.fail_json.assert_called_with(
            msg='No anti affinity policy was found with policy name: nothing')

    @patch.object(clc_common, 'call_clc_api')
    def test_find_aa_policy_id_duplicate_match(self, mock_call_api):
        mock_call_api.return_value = {
            'items': [{'name': 'test1', 'id': '111'},
                      {'name': 'test2', 'id': '222'},
                      {'name': 'test1', 'id': '111'}]}

        under_test = ClcServer(self.module)
        under_test.clc_auth = {'clc_alias': 'mock_alias'}
        under_test.module.params = {'anti_affinity_policy_name': 'test1'}

        policy_id = under_test._find_aa_policy_id()
        under_test.module.fail_json.assert_called_with(
            msg='Multiple anti affinity policies found for name: test1')

    @patch.object(clc_common, 'call_clc_api')
    def test_find_aa_policy_id_get_fail(self, mock_call_api):
        error = ClcApiException()
        error.message = 'Mock failure message'
        mock_call_api.side_effect = error
        under_test = ClcServer(self.module)
        under_test.clc_auth = {'clc_alias': 'mock_alias'}
        under_test.module.params = {'anti_affinity_policy_id': 'mock_id'}
        under_test._find_aa_policy_id()
        self.module.fail_json.assert_called_with(
            msg='Unable to fetch anti affinity policies for '
                'account: mock_alias. Mock failure message')

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

    @patch.object(clc_common, 'call_clc_api')
    def test_find_datacenter_no_location(self, mock_call_api):
        params = {
            'state': 'present',
        }
        under_test = ClcServer(self.module)
        under_test.module.params = params
        under_test.clc_auth = {'clc_alias': 'dummy_alias',
                               'clc_location': 'dummy_location'}
        ret = under_test._find_datacenter()
        self.assertEqual(ret, 'dummy_location')

    @patch.object(clc_common, 'authenticate')
    def test_find_datacenter_exception(self, mock_authenticate):
        error = ClcApiException()
        mock_authenticate.side_effect = error
        params = {
            'state': 'present',
            'location': 'testdc'
        }
        under_test = ClcServer(self.module)
        under_test.module.params = params
        under_test._find_datacenter()
        self.module.fail_json.assert_called_with(
            msg='Unable to find location: testdc')

    @patch.object(clc_common, 'find_group')
    def test_find_group_no_result(self, mock_find_group):
        datacenter = 'testdc'
        mock_find_group.side_effect = ClcApiException()

        under_test = ClcServer(self.module)
        under_test.root_group = mock.MagicMock()
        ret = under_test._find_group(datacenter, 'lookup_group')
        self.module.fail_json.assert_called_with(
            msg='Unable to find group: lookup_group in location: testdc')
        self.assertEqual(ret, None)

    def test_find_cpu_exception(self):
        params = {
            'state': 'present'
        }
        mock_group = mock.MagicMock()
        under_test = ClcServer(self.module)
        under_test.module.params = params
        under_test._group_default_value = mock.MagicMock()
        under_test._group_default_value.return_value = None
        under_test._find_cpu(mock_group)
        self.module.fail_json.assert_called_with(
            msg="Can't determine a default cpu value. "
                "Please provide a value for cpu.")

    def test_find_memory_exception(self):
        params = {
            'state': 'present'
        }
        mock_group = mock.MagicMock()
        under_test = ClcServer(self.module)
        under_test.module.params = params
        under_test._group_default_value = mock.MagicMock()
        under_test._group_default_value.return_value = None
        under_test._find_memory(mock_group)
        self.module.fail_json.assert_called_with(
            msg="Can't determine a default memory value. "
                "Please provide a value for memory.")

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

    def test_find_ttl(self):
        params = {
            'state': 'present',
            'ttl': 5000
        }
        self.module.params = params
        res = ClcServer._find_ttl(self.module)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_server, 'datetime')
    def test_find_ttl_exception(self, mock_datetime):
        params = {
            'state': 'present',
            'ttl': 1000
        }
        self.module.params = params
        ClcServer._find_ttl(self.module)
        self.module.fail_json.assert_called_with(msg='Ttl cannot be <= 3600')

    def test_startstop_servers_invalid_list(self):
        under_test = ClcServer(self.module)
        under_test._start_stop_servers({'id': 'value'})
        self.module.fail_json.assert_called_with(
            msg='server_ids should be a list of servers, aborting')

    def test_delete_servers_invalid_list(self):
        ClcServer._delete_servers(self.module, self.clc, {'id': 'value'})
        self.module.fail_json.assert_called_with(msg='server_ids should be a list of servers, aborting')

    @patch.object(clc_server, 'clc_common')
    @patch.object(ClcServer, '_validate_module_params')
    def test_process_request_absent_state_w_invalid_servers(self, mock_validate,
                                                            mock_clc_common):
        params = {
            'state': 'absent',
            'server_ids': {'data': 'invalid'}
        }
        mock_validate.return_value = params
        under_test = ClcServer(self.module)
        under_test.process_request()
        self.module.fail_json.assert_called_with(msg="server_ids needs to be a list of instances to delete: {'data': 'invalid'}")

    @patch.object(clc_server, 'clc_common')
    @patch.object(ClcServer, '_validate_module_params')
    def test_process_request_started_state_w_invalid_servers(self,
                                                             mock_validate,
                                                             mock_clc_common):
        params = {
            'state': 'started',
            'server_ids': {'data': 'invalid'}
        }
        mock_validate.return_value = params
        under_test = ClcServer(self.module)
        under_test.process_request()
        self.module.fail_json.assert_called_with(msg="server_ids needs to be a list of servers to run: {'data': 'invalid'}")

    @patch.object(clc_server, 'clc_common')
    @patch.object(ClcServer, '_validate_module_params')
    def test_process_request_present_state_w_no_template(self, mock_validate,
                                                         mock_clc_common):
        params = {
            'state': 'present',
            'server_ids': ['id1', 'id2']
        }
        mock_validate.return_value = params
        under_test = ClcServer(self.module)
        under_test.process_request()
        self.module.fail_json.assert_called_with(msg='template parameter is required for new instance')

    @patch.object(clc_common, 'call_clc_api')
    def test_add_alert_policy_to_server_exception(self, mock_call_api):
        error = ClcApiException('Mock failure message')
        mock_call_api.side_effect = error
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        server_params = {
            'name': 'test server'
        }
        self.assertRaises(ClcApiException,
                          under_test._add_alert_policy_to_server,
                          'server_id',
                          'alert_policy_id')

    @patch.object(clc_common, 'call_clc_api')
    def test_get_alert_policy_id_by_name_dup_match(self, mock_call_api):
        mock_call_api.return_value = {
            'items': [{'name' : 'test1', 'id' : '111'},
                      {'name' : 'test2', 'id' : '222'},
                      {'name' : 'test1', 'id' : '111'}]}

        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'dummy_alias'
        under_test._get_alert_policy_id_by_name('test1')
        self.module.fail_json.assert_called_with(
            msg='multiple alert policies were found with policy name : test1')

    @patch.object(clc_common, 'call_clc_api')
    def test_get_alert_policy_id_by_name(self, mock_call_api):
        mock_call_api.return_value = {
            'items': [{'name': 'test1', 'id': '111'},
                      {'name': 'test2', 'id': '222'}]}

        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'dummy_alias'
        policy_id = under_test._get_alert_policy_id_by_name('test1')
        self.assertEqual('111', policy_id)

    @patch.object(clc_common, 'call_clc_api')
    def test_change_server_power_state_started(self, mock_call_api):
        server = mock.MagicMock()
        server.id = 'server1'
        response = [{'server': 'server1', 'isQueued': False}]
        mock_call_api.return_value = response
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        result = under_test._change_server_power_state(server, 'started')
        self.assertEqual(result, response)
        mock_call_api.assert_called_once_with(
            under_test.module, under_test.clc_auth,
            'POST', '/operations/mock_alias/servers/powerOn',
            data=[server.id])
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(clc_common, 'call_clc_api')
    def test_change_server_power_state_stopped(self, mock_call_api):
        server = mock.MagicMock()
        server.id = 'server1'
        response = [{'server': 'server1', 'isQueued': False}]
        mock_call_api.return_value = response
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        result = under_test._change_server_power_state(server, 'stopped')
        self.assertEqual(result, response)
        mock_call_api.assert_called_once_with(
            under_test.module, under_test.clc_auth,
            'POST', '/operations/mock_alias/servers/shutDown',
            data=[server.id])
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(clc_common, 'call_clc_api')
    def test_change_server_power_state_error(self, mock_call_api):
        error = ClcApiException('Failed')
        server = mock.MagicMock()
        server.id = 'server1'
        mock_call_api.side_effect = error
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        result = under_test._change_server_power_state(server, 'stopped')
        self.assertEqual(result, None)
        self.module.fail_json.assert_called_with(msg='Unable to change power state for server server1')

    @patch.object(clc_common, 'call_clc_api')
    def test_add_alert_policy_to_servers(self, mock_call_api):
        params = {
            'alert_policy_id': '123',
        }
        self.module.params = params
        self.module.check_mode = False
        server = mock.MagicMock()
        server.id = 'server1'
        servers = [server]
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'test'
        result = under_test._add_alert_policy_to_servers(servers)
        self.assertEqual(result, [])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_add_alert_policy_to_servers_error(self, mock_call_api):
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error
        params = {
            'alert_policy_id': '123',
        }
        self.module.params = params
        self.module.check_mode = False
        server = mock.MagicMock()
        server.id = 'server1'
        servers = [server]
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'test'
        result = under_test._add_alert_policy_to_servers(servers)
        self.assertEqual(result, servers)
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
        assert mock_ClcServer_instance.process_request.call_count == 1

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

    @patch.object(ClcServer, '_find_datacenter')
    def test_enforce_count_missing_argument(self, mock_find_datacenter):
        params = {
            'state': 'present',
            'exact_count': 1
        }
        self.module.params = params
        under_test = ClcServer(self.module)
        under_test._enforce_count(self.module, self.clc)
        self.module.fail_json.assert_called_with(msg="you must use the 'count_group' option with exact_count")

    @patch.object(ClcServer, '_find_datacenter')
    @patch.object(ClcServer, '_find_running_servers_by_group')
    def test_enforce_count_no_change(self, mock_running_servers,
                                     mock_find_datacenter):
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

    @patch.object(clc_common, 'call_clc_api')
    def test_add_public_ip_to_servers_w_failed_servers(self, mock_call_api):
        mock_server = mock.MagicMock()
        mock_server.id = 'server1'
        mock_call_api.side_effect = ClcApiException()
        mock_server.PublicIPs().Add.side_effect = APIFailedResponse()
        servers = [mock_server]
        self.module.check_mode = False
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        failed_servers = under_test._add_public_ip_to_servers(
                                             True, servers,
                                             'TCP',
                                             [80])
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(len(failed_servers), 1)
        self.assertEqual(failed_servers[0].id, 'server1')

    @patch.object(ClcServer, '_find_datacenter')
    @patch.object(ClcServer, '_create_servers')
    @patch.object(ClcServer, '_find_running_servers_by_group')
    def test_enforce_count_min_count(self, mock_running_servers,
                                     mock_create_servers, mock_find_datacenter):
        mock_server_list = [mock.MagicMock()]
        mock_create_servers.return_value = ('test_server', mock_server_list, mock_server_list, True)
        mock_running_servers.return_value = (mock_server_list, mock_server_list)
        params = {
            'min_count': 2,
            'count_group': 'test'
        }
        self.module.params = params
        under_test = ClcServer(self.module)
        server_dict_array, changed_server_ids, partial_servers_ids, changed = \
            under_test._enforce_count(self.module, self.clc)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(changed, True)
        self.assertEqual(server_dict_array, 'test_server')

    @patch.object(ClcServer, '_find_datacenter')
    @patch.object(ClcServer, '_delete_servers')
    @patch.object(ClcServer, '_find_running_servers_by_group')
    def test_enforce_count_max_count(self, mock_running_servers,
                                     mock_delete_servers, mock_find_datacenter):
        mock_server_list = [mock.MagicMock()]
        mock_server_list[0].id = 'mockid1'
        mock_server_list.append(mock.MagicMock())
        mock_server_list[1].id = 'mockid2'
        mock_delete_servers.return_value = (True, {}, 'mockid1')
        mock_running_servers.return_value = (mock_server_list, mock_server_list)
        params = {
            'max_count': 1,
            'count_group': 'test'
        }
        self.module.params = params
        under_test = ClcServer(self.module)
        server_dict_array, changed_server_ids, partial_servers_ids, changed = \
            under_test._enforce_count(self.module, self.clc)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(changed, True)

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

    @patch.object(ClcServer, '_change_server_power_state')
    @patch.object(ClcServer, '_refresh_servers')
    @patch.object(clc_common, 'servers_by_id')
    def test_start_stop_servers(self, mock_servers_by_id, mock_refresh,
                                mock_power_state):
        params = {
            'wait': False
        }
        self.module.params = params
        mock_server = mock.MagicMock()
        mock_server.id = 'mockid1'
        mock_servers = [mock_server]
        mock_servers_by_id.return_value = mock_servers
        self.module.check_mode = False
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        under_test._refresh_servers.return_value = mock_servers
        changed, server_dict_array, result_server_ids = \
            under_test._start_stop_servers(['server1', 'server2'])
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(changed, True)
        self.assertEqual(result_server_ids, ['mockid1'])

    def test_wait_for_requests_fail(self):
        under_test = ClcServer(self.module)
        mock_request = mock.MagicMock()
        mock_request.WaitUntilComplete.return_value = 1
        under_test._wait_for_requests(self.module, [mock_request])
        self.module.fail_json.assert_called_with(msg='Unable to process server request')

    @patch.object(clc_common, 'servers_by_id')
    def test_refresh_servers_fail(self, mock_servers_by_id):
        error = ClcApiException()
        error.message = 'Mock fail message'
        under_test = ClcServer(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        mock_server = mock.MagicMock()
        mock_server.id = 'mock_server_id'
        mock_servers_by_id.side_effect = [error]
        mock_servers = [mock_server]
        under_test._refresh_servers(mock_servers)
        self.module.fail_json.assert_called_with(
            msg='Unable to refresh servers. Mock fail message')

    @patch.object(clc_server, 'clc_common')
    def test_find_alias_exception(self, mock_clc_common):
        error = ClcApiException()
        error.message = 'Mock fail message'
        mock_clc_common.authenticate.side_effect = error
        self.module.params = {}
        under_test = ClcServer(self.module)
        under_test._find_alias()
        self.module.fail_json.assert_called_with(msg='Unable to find account alias. Mock fail message')


if __name__ == '__main__':
    unittest.main()
