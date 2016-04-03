#!/usr/bin/env python
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

import clc_ansible_module.clc_network as clc_network
from clc_ansible_module.clc_network import ClcNetwork
import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch, create_autospec
import os
import unittest

def FakeAnsibleModule():
    module = mock.MagicMock()
    module.check_mode = False
    module.params = {}
    return module

class TestClcNetwork(unittest.TestCase):

    def setUp(self):

        existing_net = mock.MagicMock()
        v2_networks = mock.MagicMock()
        v2_networks.Get = mock.MagicMock(side_effect=lambda key: existing_net if key=="existing" else None)
        self.mock_nets = v2_networks

        self.module = FakeAnsibleModule()
        self.network = ClcNetwork(self.module)
        self.network.module.exit_json = mock.MagicMock()
        self.network_dict = {}
        self.network.clc.v2.Networks = mock.MagicMock()

    # Begin copy/pasta tests

    def test_api_set_credentials(self):
        self.network.clc.v2.SetCredentials = mock.MagicMock()
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME':'passWORD', 'CLC_V2_API_PASSWD':'UsErnaME'}):
            try:
                self.network.process_request()
            except:
                # It'll die, and we don't care
                pass

        self.network.clc.v2.SetCredentials.assert_called_once_with(api_username='passWORD',api_passwd='UsErnaME')

    @patch.object(clc_network, 'clc_sdk')
    def test_set_user_agent(self, mock_clc_sdk):
        clc_network.__version__ = "1"
        ClcNetwork._set_user_agent(mock_clc_sdk)

        self.assertTrue(mock_clc_sdk.SetRequestsSession.called)

    @patch.object(ClcNetwork, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            self.module.fail_json.called = False
            under_test = ClcNetwork(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcNetwork, 'clc')
    def test_set_clc_credentials_w_creds(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'dummyuser', 'CLC_V2_API_PASSWD': 'dummypwd'}):
            under_test = ClcNetwork(self.module)
            under_test._set_clc_credentials_from_env()
            mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='dummyuser', api_passwd='dummypwd')

    @patch.object(ClcNetwork, 'clc')
    def test_set_clc_credentials_w_api_url(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_URL': 'dummyapiurl'}):
            under_test = ClcNetwork(self.module)
            under_test._set_clc_credentials_from_env()
            self.assertEqual(under_test.clc.defaults.ENDPOINT_URL_V2, 'dummyapiurl')

    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcNetwork(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(self.module.fail_json.called, True)

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_network)
            clc_network.ClcNetwork(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')
        reload(clc_network)

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
            reload(clc_network)
            clc_network.ClcNetwork(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library  version should be >= 2.5.0')
        reload(clc_network)

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
            reload(clc_network)
            clc_network.ClcNetwork(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library is required for this module')
        reload(clc_network)

    @patch.object(clc_network, 'AnsibleModule')
    @patch.object(clc_network, 'ClcNetwork')
    def test_main(self, mock_ClcNetwork, mock_AnsibleModule):
        mock_ClcNetwork_instance        = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcNetwork.return_value    = mock_ClcNetwork_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_network.main()

        mock_ClcNetwork.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcNetwork_instance.process_request.call_count ==1


    # End copy/pasta tests


    def test_argument_spec_contract(self):
        args = ClcNetwork._define_module_argument_spec()
        self.assertEqual(args, dict(
            name=dict(required=True),
            location=dict(required=True),
            description=dict(required=False),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(default=True)
        ))

    @patch.object(ClcNetwork, '_set_clc_credentials_from_env')
    def test_process_request_populates_network_list(self, mock_set_creds):
        mock_nets = mock.MagicMock()
        self.network.clc.v2.Networks = mock.MagicMock(return_value=mock_nets)
        self.module.params = {
            'name': 'nope',
            'location': 'mock_loc'
        }

        self.network.process_request()

        self.network.clc.v2.Networks.assert_called_once_with(location="mock_loc")
        self.assertEqual(mock_nets, self.network.networks)

    @patch.object(ClcNetwork, '_set_clc_credentials_from_env')
    def test_process_request_for_create_calls_sdk_network_create(self, mock_set_creds):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            self.network.clc.v2.Network.Create = mock.MagicMock()
            self.module.params = {
                'name': 'nope',
                'location': 'mock_loc'
            }

            self.network.process_request()

            self.network.clc.v2.Network.Create.assert_called_once_with(location="mock_loc")

    @patch.object(ClcNetwork, '_set_clc_credentials_from_env')
    def test_process_request_for_create_waits_on_request(self, mock_set_creds):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            mock_request = mock.MagicMock()
            mock_request.WaitUntilComplete = mock.MagicMock(return_value=0)
            self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_request)
            self.module.params = {
                'name': 'nope',
                'location': 'mock_loc'
            }

            self.network.process_request()

            self.assertEqual(1, mock_request.WaitUntilComplete.call_count)
            self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcNetwork, '_set_clc_credentials_from_env')
    def test_process_request_for_create_waits_on_request(self, mock_set_creds):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            mock_request = mock.MagicMock()
            mock_request.WaitUntilComplete = mock.MagicMock(return_value=1)
            self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_request)
            self.module.params = {
                'name': 'nope',
                'location': 'mock_loc'
            }

            self.network.process_request()

            self.assertEqual(1, mock_request.WaitUntilComplete.call_count)
            self.module.fail_json.assert_called_once_with(msg="Unable to create network")

    @patch.object(ClcNetwork, '_set_clc_credentials_from_env')
    def test_process_request_for_create_skips_wait_when_wait_false(self, mock_set_creds):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            mock_request = mock.MagicMock()
            mock_request.WaitUntilComplete = mock.MagicMock(return_value=0)
            self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_request)
            self.module.params = {
                'name': 'nope',
                'location': 'mock_loc',
                'wait': False
            }

            self.network.process_request()

            self.assertEqual(0, mock_request.WaitUntilComplete.call_count)

    @patch.object(ClcNetwork, '_set_clc_credentials_from_env')
    def test_process_request_for_create_skips_create_when_network_exists(self, mock_set_creds):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets):
            mock_request = mock.MagicMock()
            mock_request.WaitUntilComplete = mock.MagicMock(return_value=0)
            self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_request)
            self.module.params = {
                'name': 'existing',
                'location': 'mock_loc',
            }

            self.network.process_request()

            self.assertEqual(0, self.network.clc.v2.Network.Create.call_count)
            self.module.exit_json.assert_called_once_with(changed=False,network=None)

    @patch.object(ClcNetwork, '_set_clc_credentials_from_env')
    def test_process_request_for_create_exits_with_expected_network(self, mock_set_creds):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets):
            mock_nets = mock.MagicMock()
            mock_new = mock.MagicMock()
            mock_new.id = '12345'
            mock_new.alias = 'my_alias'
            mock_new.data = {
                'name': 'working',
                'field': 'value'
            }
            mock_nets.Get = mock.MagicMock(return_value = mock_new)
            self.network.clc.v2.Networks = mock.MagicMock(return_value=mock_nets)

            mock_request = mock.MagicMock()
            mock_request.WaitUntilComplete = mock.MagicMock(return_value=0)
            self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_request)
            self.module.params = {
                'name': 'working',
                'location': 'mock_loc'
            }

            self.network.process_request()

            self.module.exit_json.assert_called_once_with(changed=True,network=mock_new.data)


if __name__ == '__main__':
    unittest.main()
