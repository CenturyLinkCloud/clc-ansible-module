#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import os
import unittest
import mock
from mock import patch

import clc_ansible_module.clc_server_fact as clc_server_fact
from clc_ansible_module.clc_server_fact import ClcServerFact

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class TestClcServerFactFunctions(unittest.TestCase):

    def setUp(self):
        self.module = mock.MagicMock()
        self.clc_auth = {'clc_alias': 'mock_alias', 'clc_location': 'mock_dc'}

        server = mock.MagicMock()
        server.id = 'mock_id'
        server.data = {'id': 'mock_id'}
        self.server = server

    @patch.object(ClcServerFact, '_get_server_credentials')
    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'server_ip_addresses')
    @patch.object(clc_common, 'find_server')
    def test_process_request_without_credentials(self, mock_find_server,
                                                 mock_ip_addresses,
                                                 mock_authenticate,
                                                 mock_server_credentials):
        mock_authenticate.return_value = self.clc_auth
        mock_find_server.return_value = self.server
        mock_ip_addresses.return_value = self.server

        under_test = ClcServerFact(self.module)
        under_test.module.params = {'server_id': 'mock_id'}

        under_test.process_request()

        self.assertFalse(mock_server_credentials.called)
        self.module.exit_json.assert_called_once_with(
            changed=False, server=self.server.data)

    @patch.object(ClcServerFact, '_get_server_credentials')
    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'server_ip_addresses')
    @patch.object(clc_common, 'find_server')
    def test_process_request_with_credentials(self, mock_find_server,
                                              mock_ip_addresses,
                                              mock_authenticate,
                                              mock_server_credentials):
        mock_authenticate.return_value = self.clc_auth
        mock_find_server.return_value = self.server
        mock_ip_addresses.return_value = self.server
        credentials = {'userName': 'mock_user', 'password': 'mock_passwd'}
        mock_server_credentials.return_value = credentials
        server_data = self.server.data.copy()
        server_data['credentials'] = credentials

        under_test = ClcServerFact(self.module)
        under_test.module.params = {'server_id': 'mock_id',
                                    'credentials': True}

        under_test.process_request()

        self.assertTrue(mock_server_credentials.called)
        self.module.exit_json.assert_called_once_with(
            changed=False, server=server_data)

    @patch.object(clc_common, 'call_clc_api')
    def test_get_server_credentials(self, mock_call_api):
        credentials = {'userName': 'mock_user', 'password': 'mock_passwd'}
        mock_call_api.return_value = credentials

        under_test = ClcServerFact(self.module)
        under_test.clc_auth = self.clc_auth

        response = under_test._get_server_credentials('mock_id')

        self.assertEqual(response, credentials)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_get_server_credentials_exception(self, mock_call_api):
        error = ClcApiException('Fail')
        mock_call_api.side_effect = error

        under_test = ClcServerFact(self.module)
        under_test.clc_auth = self.clc_auth

        under_test._get_server_credentials('mock_id')

        self.module.fail_json.assert_called_once_with(
            msg='Unable to fetch the credentials for server id: mock_id. Fail')

    def test_define_argument_spec(self):
        result = ClcServerFact._define_module_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertTrue('argument_spec' in result)
        self.assertEqual(
            result['argument_spec'],
            {'server_id': {'type': 'str', 'required': True},
             'credentials': {'type': 'bool', 'default': False}})

    @patch.object(clc_server_fact, 'AnsibleModule')
    @patch.object(clc_server_fact, 'ClcServerFact')
    def test_main(self, mock_ClcServerFact, mock_AnsibleModule):
        mock_ClcServerFact_instance = mock.MagicMock()
        mock_AnsibleModule_instance = mock.MagicMock()
        mock_ClcServerFact.return_value = mock_ClcServerFact_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_server_fact.main()

        mock_ClcServerFact.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcServerFact_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()
