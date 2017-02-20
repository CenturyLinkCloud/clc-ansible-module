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

import mock
from mock import patch
import unittest

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import clc_ansible_module.clc_blueprint_package as clc_blueprint_package
from clc_ansible_module.clc_blueprint_package import ClcBlueprintPackage


class TestClcBluePrintPackageFunctions(unittest.TestCase):

    def setUp(self):
        self.clc_auth = {'clc_alias': 'mock_alias', 'clc_location': 'mock_dc'}
        self.module = mock.MagicMock()

        # Mock Servers
        mock_server1 = mock.MagicMock()
        mock_server1.id = 'TESTSVR1'
        self.mock_server1 = mock_server1
        mock_server2 = mock.MagicMock()
        mock_server2.id = 'TESTSVR2'
        self.mock_server2 = mock_server2

    def test_define_argument_spec(self):
        result = ClcBlueprintPackage.define_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(clc_common, 'authenticate')
    @patch.object(ClcBlueprintPackage, '_wait_for_requests_to_complete')
    @patch.object(ClcBlueprintPackage, 'ensure_package_installed')
    def test_process_request_w_valid_args(self, mock_ensure_installed,
                                          mock_wait, mock_authenticate):
        server_ids = [self.mock_server1.id, self.mock_server2.id]
        test_params = {
            'server_ids': server_ids,
            'package_id': 'TSTPKGID1',
            'package_params': {},
            'state': 'present'
        }
        self.module.params = test_params
        self.module.check_mode = False
        mock_ensure_installed.return_value = (True, server_ids, [])

        under_test = ClcBlueprintPackage(self.module)
        under_test.process_request()

        self.assertTrue(mock_authenticate.called)
        self.module.exit_json.assert_called_once_with(
            changed=True, server_ids=server_ids)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcBlueprintPackage, 'clc_install_package')
    def test_ensure_package_installed(self, mock_install_package,
                                      mock_get_servers_from_clc):
        mock_server_list = [self.mock_server1, self.mock_server2]
        mock_get_servers_from_clc.return_value = mock_server_list
        mock_response = mock.MagicMock()
        mock_install_package.return_value = mock_response

        under_test = ClcBlueprintPackage(self.module)
        under_test.module.check_mode = False

        changed, return_servers, requests = under_test.ensure_package_installed(
            [self.mock_server1.id, self.mock_server2.id],
            'dummyId', {})

        self.assertTrue(mock_get_servers_from_clc.called)
        self.assertFalse(self.module.fail_json.called)
        self.assertTrue(changed)
        self.assertEqual(return_servers,
                         [self.mock_server1.id, self.mock_server2.id])
        self.assertEqual(len(requests), 2)

    @patch.object(clc_common, 'servers_by_id')
    @patch.object(ClcBlueprintPackage, 'clc_install_package')
    def test_ensure_package_installed_no_servers(self, mock_install_package,
                                                 mock_get_servers_from_clc):
        mock_server_list = []
        mock_get_servers_from_clc.return_value = mock_server_list
        mock_response = mock.MagicMock()
        mock_install_package.return_value = mock_response

        under_test = ClcBlueprintPackage(self.module)
        under_test.module.check_mode = False

        changed, return_servers, requests = under_test.ensure_package_installed(
            [], 'dummyId', {})

        self.assertTrue(mock_get_servers_from_clc.called)
        self.assertFalse(self.module.fail_json.called)
        self.assertFalse(changed)
        self.assertEqual(return_servers, [])
        self.assertEqual(len(requests), 0)

    @patch.object(clc_common, 'wait_on_completed_operations')
    def test_wait_for_request(self, mock_wait):
        mock_wait.return_value = 1
        under_test = ClcBlueprintPackage(self.module)
        under_test.module.params = {'wait': True}

        under_test._wait_for_requests_to_complete([mock.MagicMock()])

        self.module.fail_json.assert_called_once_with(
            msg='Unable to process blueprint request')

    @patch.object(clc_common, 'call_clc_api')
    def test_clc_install_package(self, mock_call_api):
        self.module.check_mode = False
        mock_response = mock.MagicMock()
        mock_call_api.return_value = mock_response

        under_test = ClcBlueprintPackage(self.module)
        under_test.clc_auth = self.clc_auth

        result = under_test.clc_install_package(self.mock_server1,
                                                'package_id', {})

        self.assertEqual(result, mock_response)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_clc_install_package_exception(self, mock_call_api):
        self.module.check_mode = False
        mock_call_api.side_effect = ClcApiException('Mock failure message')

        under_test = ClcBlueprintPackage(self.module)
        under_test.clc_auth = self.clc_auth

        under_test.clc_install_package(self.mock_server1, 'package_id', {})

        self.module.fail_json.assert_called_once_with(
            msg='Failed to install package: package_id to server {id}. '
                'Mock failure message'.format(id=self.mock_server1.id))

    @patch.object(clc_blueprint_package, 'AnsibleModule')
    @patch.object(clc_blueprint_package, 'ClcBlueprintPackage')
    def test_main(self, mock_ClcPackage, mock_AnsibleModule):
        mock_ClcPackage_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcPackage.return_value   = mock_ClcPackage_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_blueprint_package.main()

        mock_ClcPackage.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcPackage_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()
