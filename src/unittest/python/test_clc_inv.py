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

import clc_inv
from clc import CLCException
import clc as clc_sdk
import mock
from mock import patch
from mock import create_autospec
import unittest

class TestClcInvFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter=mock.MagicMock()

    @patch('clc_inv.clc')
    def test_find_hostvars_single_server_none(self, mock_clc_sdk):
        server = mock.MagicMock()
        server.name = 'testServerWithNoDetails'
        server.data = {}
        mock_clc_sdk.v2.Server.return_value = server
        result = clc_inv._find_hostvars_single_server('testServerWithNoDetails')
        self.assertIsNone(result)

    @patch('clc_inv.clc')
    def test_find_hostvars_single_server(self, mock_clc_sdk):
        server = mock.MagicMock()
        server.name = 'testServerWithNoDetails'
        server.data = {'details':
                           {'ipAddresses':
                                [
                                    {'internal':'true'}
                                ]
                           }
                        }
        mock_clc_sdk.v2.Server.return_value = server
        result = clc_inv._find_hostvars_single_server('testServerWithNoDetails')
        self.assertIsNone(result)

    def test_find_hostvars_single_server_uses_unique_session(self):
        pass

    @patch.object(clc_inv, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            clc_inv._set_clc_credentials_from_env()
        self.assertEqual(clc_inv.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    def test_is_list_flat(self):
        list = [1,2,3]
        res = clc_inv._is_list_flat(list)
        self.assertEqual(res, True)

    def test_flatten_list(self):
        list = [1,2,3]
        res = clc_inv._flatten_list(list)
        self.assertEqual(res, [1,2,3])

    @patch('clc_inv._find_all_groups')
    @patch('clc_inv._get_servers_from_groups')
    @patch('clc_inv._find_all_hostvars_for_servers')
    @patch('clc_inv._build_hostvars_dynamic_groups')
    @patch('clc_inv._set_clc_credentials_from_env')
    def test_print_inventory_json(self, mock_creds, mock_hostvars_d, mock_hostvars, mock_servers, mock_groups):
        try:
            mock_groups.return_value = {'groups':['group1', 'group2']}
            mock_servers.return_value = ['server1', 'server2']
            mock_hostvars.return_value = ['var1', 'var2']
            mock_hostvars_d.return_value = {'dgroups':['dg1', 'dg2']}
            clc_inv.print_inventory_json()
        except:
            self.fail('Exception was thrown when it was not expected')

    @patch('clc_inv._flatten_list')
    def test_parse_groups_result_to_dict_empty(self, mock_flatten):
        try:
            input = [mock.MagicMock()]
            mock_flatten.return_value = 'OK'
            res = clc_inv._parse_groups_result_to_dict(input)
            self.assertEqual(res, {})
        except:
            self.fail('Exception was thrown when it was not expected')

    def test_build_datacenter_groups(self):
        try:
            input = {
                'hostvars' : {
                    'server1' : {
                        'clc_data' : {
                            'locationId': 'UC1'
                        }
                    }
                }
            }
            res = clc_inv._build_datacenter_groups(input)
            self.assertEqual(res, {'UC1': ['server1']})
        except:
            self.fail('Exception was thrown when it was not expected')

    @patch('clc_inv._build_datacenter_groups')
    def test_build_hostvars_dynamic_groups(self, mock_build):
            input = 'test'
            mock_build.return_value = {'status': 'OK'}
            res = clc_inv._build_hostvars_dynamic_groups(input)
            self.assertEqual(res, {'status': 'OK'})

    @patch('clc_inv._add_windows_hostvars')
    @patch('clc_inv.clc')
    def test_add_windows_hostvars(self, mock_clc_sdk, mock_add_windows_hostvars):
        server = mock.MagicMock()
        server.name = 'testWindowsServer'
        server.data = {'clc_data': {
            'os': 'windows_os_image'
        }}
        hostvars = {server.name: { 'clc_data': {
            'os': 'windows_os_image'
        }}}
        mock_add_windows_hostvars.return_value = { 'testWindowsServer': {'ansible_ssh_port': 5986, 'clc_data': {'os': 'windows_os_image'}, 'ansible_connection': 'winrm'} }

        mock_clc_sdk.v2.Server.return_value = server
        result = clc_inv._add_windows_hostvars(hostvars, server)
        self.assertEquals(result[server.name]['ansible_ssh_port'], 5986)
        self.assertEquals(result[server.name]['ansible_connection'], 'winrm')

    @patch('clc_inv._add_windows_hostvars')
    @patch('clc_inv.clc')
    def test_add_windows_hostvars_to_linux(self, mock_clc_sdk, mock_add_windows_hostvars):
        server = mock.MagicMock()
        server.name = 'testLinuxServer'
        server.data = {'clc_data': {
            'os': 'linux_os_image'
        }}
        hostvars = {server.name: { 'clc_data': {
            'os': 'linux_os_image'
        }}}
        mock_add_windows_hostvars.return_value = { 'testLinuxServer': {'clc_data': {'os': 'linux_os_image'}} }

        mock_clc_sdk.v2.Server.return_value = server
        result = clc_inv._add_windows_hostvars(hostvars, server)
        self.assertNotIn('ansible_ssh_port', result[server.name])
        self.assertNotIn('ansible_connection', result[server.name])
if __name__ == '__main__':
    unittest.main()
