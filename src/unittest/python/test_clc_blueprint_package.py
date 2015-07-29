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

import clc_ansible_module.clc_blueprint_package as clc_blueprint_package
from clc_ansible_module.clc_blueprint_package import ClcBlueprintPackage
import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch
from mock import create_autospec
import unittest

class TestClcBluePrintPackageFunctions(unittest.TestCase):


    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        reload(clc_blueprint_package)


    #TODO: Put this in a Util/test_data class
    def build_mock_server_list(self):
        # Mock Add IP Requests
        mock_req1 = mock.MagicMock()
        mock_req2 = mock.MagicMock()
        # Mock PublicIps
        pubip1 = mock.MagicMock()
        pubip2 = mock.MagicMock()
        pubip1.id = '10.10.10.10'
        pubip1.internal = '9.10.11.12'
        pubip2.id = '11.11.11.11'
        pubip2.internal = '13.14.15.16'
        # Mock Servers
        mock_server1 = mock.MagicMock()
        mock_server2 = mock.MagicMock()
        mock_server1.id = 'TESTSVR1'
        mock_server1.data = {'details': {'ipAddresses': [{'internal': '1.2.3.4'}]}}
        mock_server1.PublicIPs().public_ips = [pubip1]
        pubip1.Delete.return_value = mock_req1
        mock_req1.server = mock_server1
        mock_req1.requests = [mock_req1]
        mock_server1.PublicIPs().Add.return_value = mock_req1
        mock_server2.id = 'TESTSVR2'
        mock_server2.data = {'details': {'ipAddresses': [{'internal': '5.6.7.8'}]}}
        mock_server2.PublicIPs().public_ips = [pubip2]
        pubip2.Delete.return_value = mock_req2
        mock_req2.server = mock_server2
        mock_req2.requests = [mock_req2]
        mock_server2.PublicIPs().Add.return_value = mock_req2
        # Mock Package
        package1 = mock.MagicMock()
        package2 = mock.MagicMock()
        package1.package_id = '123'
        package1.server_ids = mock_server1
        package1.package_params = {}
        package2.package_id = '123'
        package2.server_ids = mock_server2
        package2.package_params = {}
        return [mock_server1, mock_server2]

    @patch.object(clc_blueprint_package, 'clc_sdk')
    def test_set_user_agent(self, mock_clc_sdk):
        clc_blueprint_package.__version__ = "1"
        ClcBlueprintPackage._set_user_agent(mock_clc_sdk)

        self.assertTrue(mock_clc_sdk.SetRequestsSession.called)

    @patch.object(ClcBlueprintPackage, 'clc')
    def test_set_clc_creds_w_token(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            under_test = ClcBlueprintPackage(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcBlueprintPackage, 'clc')
    def test_set_clc_credentials_w_creds(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'dummyuser', 'CLC_V2_API_PASSWD': 'dummypwd'}):
            under_test = ClcBlueprintPackage(self.module)
            under_test._set_clc_credentials_from_env()
        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='dummyuser', api_passwd='dummypwd')


    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcBlueprintPackage(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(self.module.fail_json.called, True)

    @patch.object(ClcBlueprintPackage, 'clc')
    def test_set_clc_credentials_w_api_url(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_URL': 'dummyapiurl'}):
            under_test = ClcBlueprintPackage(self.module)
            under_test._set_clc_credentials_from_env()
            self.assertEqual(under_test.clc.defaults.ENDPOINT_URL_V2, 'dummyapiurl')

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_blueprint_package)
            ClcBlueprintPackage(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')
        reload(clc_blueprint_package)

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
            reload(clc_blueprint_package)
            ClcBlueprintPackage(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library  version should be >= 2.5.0')
        reload(clc_blueprint_package)

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
            reload(clc_blueprint_package)
            ClcBlueprintPackage(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library is required for this module')
        reload(clc_blueprint_package)

    def test_define_argument_spec(self):
        result = ClcBlueprintPackage.define_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(ClcBlueprintPackage, 'clc')
    def test_get_servers_from_clc_api(self, mock_clc_sdk):
        mock_clc_sdk.v2.Servers.side_effect = CLCException("Server Not Found")
        under_test = ClcBlueprintPackage(self.module)
        under_test._get_servers_from_clc(['TESTSVR1', 'TESTSVR2'], 'FAILED TO OBTAIN LIST')
        self.module.fail_json.assert_called_once_with(msg='FAILED TO OBTAIN LIST: Server Not Found')

    @patch.object(ClcBlueprintPackage, '_set_clc_credentials_from_env')
    @patch.object(ClcBlueprintPackage, '_get_servers_from_clc')
    def test_process_request_w_valid_args(self, mock_get_servers, mock_set_clc_creds):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            , 'package_id': 'TSTPKGID1'
            , 'package_params': {}
            , 'state' : 'present'
            , 'wait' : False
        }
        mock_get_servers.return_value = [mock.MagicMock()]
        self.module.params = test_params
        self.module.check_mode = False
        under_test = ClcBlueprintPackage(self.module)
        under_test.process_request()

        self.assertTrue(mock_set_clc_creds.called)
        self.assertFalse(self.module.fail_json.called)
        self.assertTrue(self.module.exit_json.called)

    @patch.object(ClcBlueprintPackage, '_get_servers_from_clc')
    def test_ensure_package_installed_no_server(self, mock_get_servers_from_clc):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            , 'package_id': 'dummyId'
            , 'package_params': {}
            , 'state' : 'present'
        }
        server_ids = ['TESTSVR1', 'TESTSVR2']
        package_id = 'dummyId'
        package_params = {}
        self.module.params = test_params
        under_test = ClcBlueprintPackage(self.module)
        under_test.ensure_package_installed(server_ids, package_id, package_params)

        self.assertTrue(mock_get_servers_from_clc.called)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcBlueprintPackage, '_get_servers_from_clc')
    def test_ensure_package_installed(self, mock_get_servers_from_clc):
        test_params = {
            'server_ids': ['TESTSVR1', 'TESTSVR2']
            , 'package_id': 'dummyId'
            , 'package_params': {}
            , 'state' : 'present'
        }
        server_ids = ['TESTSVR1', 'TESTSVR2']
        package_id = 'dummyId'
        package_params = {}
        self.module.params = test_params
        mock_server_list = self.build_mock_server_list()
        mock_get_servers_from_clc.return_value=mock_server_list
        under_test = ClcBlueprintPackage(self.module)
        changed, return_servers, requests = under_test.ensure_package_installed(server_ids, package_id, package_params)

        self.assertTrue(mock_get_servers_from_clc.called)
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(changed, True)
        self.assertEqual(return_servers,['TESTSVR1', 'TESTSVR2'])

    def test_wait_for_requests_w_mock_request(self):
        mock_r1 = mock.MagicMock()
        mock_r1.WaitUntilComplete.return_value = True
        mock_r2 = mock.MagicMock()
        mock_r2.WaitUntilComplete.return_value = True
        requests = [mock_r1, mock_r2]
        self.module.wait = True

        under_test = ClcBlueprintPackage(self.module)
        under_test._wait_for_requests_to_complete(requests)
        self.assertFalse(self.module.fail_json.called)

    def test_wait_for_requests_w_mock_request_fail(self):
        mock_request = mock.MagicMock()
        mock_request.WaitUntilComplete.return_value = True
        mock_response = mock.MagicMock()
        mock_response.Status.return_value = 'Failed'
        mock_request.requests = [mock_response]
        requests = [mock_request]
        self.module.wait = True

        under_test = ClcBlueprintPackage(self.module)
        under_test._wait_for_requests_to_complete(requests)
        self.assertTrue(self.module.fail_json.called)

    def test_clc_install_package_exception(self):
        self.module.check_mode = False
        error = CLCException()
        error.message = 'Mock failure message'
        mock_server = mock.MagicMock()
        mock_server.id = 'server1'
        mock_server.ExecutePackage.side_effect = error
        under_test = ClcBlueprintPackage(self.module)
        under_test.clc_install_package(mock_server, 'package_id', {})
        self.module.fail_json.assert_called_once_with(msg='Failed to install package : package_id to server server1. Mock failure message')

    @patch.object(clc_blueprint_package, 'AnsibleModule')
    @patch.object(clc_blueprint_package, 'ClcBlueprintPackage')
    def test_main(self, mock_ClcPackage, mock_AnsibleModule):
        mock_ClcPackage_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcPackage.return_value   = mock_ClcPackage_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_blueprint_package.main()

        mock_ClcPackage.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcPackage_instance.process_request.assert_called_once()


if __name__ == '__main__':
    unittest.main()
