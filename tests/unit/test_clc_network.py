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

import mock
from mock import patch, create_autospec
import os
import StringIO
import json
import unittest

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import clc_ansible_module.clc_network as clc_network
from clc_ansible_module.clc_network import ClcNetwork

def FakeAnsibleModule():
    module = mock.MagicMock()
    module.check_mode = False
    module.params = {}
    return module

class TestClcNetwork(unittest.TestCase):

    def setUp(self):

        existing_net = mock.MagicMock()
        existing_net.name = 'existing'
        existing_net.id = 'existing_id'
        existing_net.data = {'name': 'existing', 'id': 'existing_id'}
        self.mock_nets = [existing_net]
        self.existing_net = existing_net

        new_net = mock.MagicMock()
        new_net.name = 'new_name'
        new_net.id = 'new_id'
        new_net.data = {'name': 'new_name', 'id': 'new_id'}
        self.new_net = new_net

        self.response_operation_uri = {
            'operationId': 'mock_op_id',
            'uri': 'mock_uri'
        }
        self.response_operation_succeeded = {
            'status': 'succeeded',
            'summary': {'links': [{
                'rel': 'network', 'id': 'mock_id'
            }]}
        }
        self.response_operation_failed = {
            'status': 'failed',
            'summary': {},
        }

        self.module = FakeAnsibleModule()
        self.clc_auth = {'v2_api_url': 'https://api.ctl.io/v2/'}
        self.network = ClcNetwork(self.module)
        self.network.module.exit_json = mock.MagicMock()

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

    def test_argument_spec_contract(self):
        args = ClcNetwork._define_module_argument_spec()
        self.assertEqual(args, dict(
            id=dict(required=False),
            name=dict(required=False),
            location=dict(required=True),
            description=dict(required=False),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(default=True, type='bool')
        ))

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'networks_in_datacenter')
    @patch.object(ClcNetwork, '_ensure_network_present')
    def test_process_request_parameters_name(self,
                                             mock_network_present,
                                             mock_networks_datacenter,
                                             mock_authenticate):
        clc_auth = {'clc_location': 'v2_loc', 'clc_alias': 'v2_alias',
                    'v2_api_url': 'https://api.ctl.io/v2/'}
        mock_authenticate.return_value = clc_auth
        mock_networks_datacenter.return_value = self.mock_nets
        mock_network_present.return_value = (False, self.existing_net)

        under_test = ClcNetwork(self.module)
        under_test.module.params = {
            'name': 'mock_name',
            'state': 'present',
        }
        under_test.process_request()

        self.assertEqual(under_test.clc_auth['clc_location'], 'v2_loc')
        mock_network_present.assert_called_once_with('v2_loc', 'mock_name')

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'networks_in_datacenter')
    @patch.object(ClcNetwork, '_ensure_network_present')
    def test_process_request_parameters_id(self,
                                           mock_network_present,
                                           mock_networks_datacenter,
                                           mock_authenticate):
        clc_auth = {'clc_location': 'v2_loc', 'clc_alias': 'v2_alias',
                    'v2_api_url': 'https://api.ctl.io/v2/'}
        mock_authenticate.return_value = clc_auth
        mock_networks_datacenter.return_value = self.mock_nets
        mock_network_present.return_value = (False, self.existing_net)

        under_test = ClcNetwork(self.module)
        under_test.module.params = {
            'id': 'mock_id',
            'name': 'mock_name',
            'location': 'mock_loc',
            'state': 'present',
        }
        under_test.process_request()

        self.assertEqual(under_test.clc_auth['clc_location'], 'mock_loc')
        mock_network_present.assert_called_once_with('mock_loc', 'mock_id')

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'networks_in_datacenter')
    @patch.object(ClcNetwork, '_ensure_network_present')
    def test_process_request_network_present(self,
                                             mock_network_present,
                                             mock_networks_datacenter,
                                             mock_authenticate):
        params = {
            'id': 'nope',
            'location': 'mock_loc'
        }
        under_test = ClcNetwork(self.module)
        under_test.module.params = params
        mock_authenticate.return_value = self.clc_auth
        mock_networks_datacenter.return_value = self.mock_nets
        mock_network_present.return_value = (True, self.new_net)
        under_test.process_request()

        # Assert
        mock_networks_datacenter.assert_called_once_with(
            self.module, self.clc_auth, 'mock_loc')
        mock_network_present.assert_called_once_with('mock_loc', 'nope')

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'networks_in_datacenter')
    @patch.object(ClcNetwork, '_ensure_network_absent')
    def test_process_request_network_absent(self,
                                            mock_network_absent,
                                            mock_networks_datacenter,
                                            mock_authenticate):
        params = {
            'id': 'nope',
            'state': 'absent',
            'location': 'mock_loc'
        }
        under_test = ClcNetwork(self.module)
        under_test.module.params = params
        mock_authenticate.return_value = self.clc_auth
        mock_networks_datacenter.return_value = self.mock_nets
        mock_network_absent.return_value = (False, self.mock_nets)
        under_test.process_request()

        # Assert
        mock_networks_datacenter.assert_called_once_with(
            self.module, self.clc_auth, 'mock_loc')
        mock_network_absent.assert_called_once_with('mock_loc', 'nope')

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'networks_in_datacenter')
    @patch.object(ClcNetwork, '_ensure_network_present')
    def test_process_request_exit_no_wait(self,
                                          mock_network_present,
                                          mock_networks_datacenter,
                                          mock_authenticate):


        mock_authenticate.return_value = self.clc_auth
        mock_networks_datacenter.return_value = self.mock_nets

        response = self.response_operation_uri
        mock_network_present.return_value = (True, self.response_operation_uri)
        expected = {
            'id': response['operationId'],
            'uri': response['uri'],
        }

        under_test = ClcNetwork(self.module)
        under_test.module.params = {
            'location': 'mock_loc',
            'state': 'present',
        }
        under_test.process_request()

        self.module.exit_json.assert_called_once_with(changed=True,network=expected)

    def test_ensure_network_absent_missing_search_key(self):
        location = 'mock_lock'
        search_key = None
        under_test = ClcNetwork(self.module)
        under_test._ensure_network_absent(location, search_key)
        self.module.fail_json.assert_called_once_with(
            msg='Must specify either a network name or id')

    def test_ensure_network_present_missing_search_key(self):
        location = 'mock_lock'
        search_key = None
        under_test = ClcNetwork(self.module)
        under_test._ensure_network_present(location, search_key)
        self.module.fail_json.assert_called_once_with(
            msg='Must specify either a network name or id')

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'find_network')
    @patch.object(ClcNetwork, '_wait_for_requests')
    @patch.object(ClcNetwork, '_update_network')
    def test_create_network_wait_with_update(self,
                                             mock_update_network,
                                             mock_wait_for_req,
                                             mock_find_network,
                                             mock_call_api):

        mock_call_api.side_effect = [self.response_operation_uri,
                                     self.response_operation_succeeded]
        mock_find_network.return_value = self.new_net
        mock_update_network.return_value = (True, self.new_net)

        params = {
            'wait': True,
            'name': 'mock_name',
            'description': 'mock_description'
        }

        under_test = ClcNetwork(self.module)
        under_test.module.params = params
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        under_test._create_network('mock_loc')

        self.assertEqual(2, mock_call_api.call_count)
        mock_wait_for_req.assert_called()
        mock_update_network.assert_called()
        self.module.fail_json.assert_not_called()

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'find_network')
    @patch.object(ClcNetwork, '_wait_for_requests')
    @patch.object(ClcNetwork, '_update_network')
    def test_create_network_wait_skip_update(self,
                                             mock_update_network,
                                             mock_wait_for_req,
                                             mock_find_network,
                                             mock_call_api):

        mock_call_api.side_effect = [self.response_operation_uri,
                                     self.response_operation_succeeded]
        mock_find_network.return_value = self.new_net
        mock_update_network.return_value = (True, self.new_net)

        params = {
            'wait': True,
        }

        under_test = ClcNetwork(self.module)
        under_test.module.params = params
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        under_test._create_network('mock_loc')

        self.assertEqual(2, mock_call_api.call_count)
        mock_wait_for_req.assert_called()
        mock_update_network.assert_not_called()
        self.module.fail_json.assert_not_called()

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'find_network')
    @patch.object(ClcNetwork, '_wait_for_requests')
    @patch.object(ClcNetwork, '_update_network')
    def test_create_network_no_wait_skip_update(self,
                                                mock_update_network,
                                                mock_wait_for_req,
                                                mock_find_network,
                                                mock_call_api):

        mock_call_api.side_effect = [self.response_operation_uri]
        mock_find_network.return_value = self.new_net

        params = {
            'wait': False,
        }

        under_test = ClcNetwork(self.module)
        under_test.module.params = params
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        under_test._create_network('mock_loc')

        self.assertEqual(1, mock_call_api.call_count)
        mock_wait_for_req.assert_called()
        mock_update_network.assert_not_called()
        self.module.fail_json.assert_not_called()

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'find_network')
    @patch.object(ClcNetwork, '_wait_for_requests')
    @patch.object(ClcNetwork, '_update_network')
    def test_create_network_operation_exception(self,
                                                mock_update_network,
                                                mock_wait_for_req,
                                                mock_find_network,
                                                mock_call_api):

        error = ClcApiException(message='FAIL')
        mock_call_api.side_effect = [error]
        mock_find_network.return_value = self.new_net

        params = {
            'wait': True,
        }

        under_test = ClcNetwork(self.module)
        under_test.module.params = params
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        under_test._create_network('mock_loc')

        self.assertEqual(1, mock_call_api.call_count)
        mock_update_network.assert_not_called()
        self.module.fail_json.assert_called_with(
            msg='Unable to claim network in location: mock_loc. FAIL')

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'find_network')
    @patch.object(ClcNetwork, '_wait_for_requests')
    @patch.object(ClcNetwork, '_update_network')
    def test_create_network_status_exception(self,
                                                mock_update_network,
                                                mock_wait_for_req,
                                                mock_find_network,
                                                mock_call_api):

        error = ClcApiException(message='FAIL')
        mock_call_api.side_effect = [self.response_operation_uri,
                                     error]
        mock_find_network.return_value = self.new_net

        params = {
            'wait': True,
        }

        under_test = ClcNetwork(self.module)
        under_test.module.params = params
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        under_test._create_network('mock_loc')

        self.assertEqual(2, mock_call_api.call_count)
        mock_update_network.assert_not_called()
        self.module.fail_json.assert_called_with(
            msg='Unable to get network operation status for operation: '
                '{id}. FAIL'.format(
                    id=self.response_operation_uri['operationId']))

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'find_network')
    @patch.object(ClcNetwork, '_wait_for_requests')
    def test_create_network_status_exception(self,
                                                mock_wait_for_req,
                                                mock_find_network,
                                                mock_call_api):

        error = ClcApiException(message='FAIL')
        mock_call_api.side_effect = [self.response_operation_uri,
                                     self.response_operation_succeeded,
                                     error]
        mock_find_network.return_value = self.new_net

        params = {
            'wait': True,
            'name': 'mock_name',
        }

        under_test = ClcNetwork(self.module)
        under_test.module.params = params
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        under_test._create_network('mock_loc')

        self.assertEqual(3, mock_call_api.call_count)
        self.module.fail_json.assert_called_with(
            msg='Unable to update network: {id} in location: {location}. '
                'FAIL'.format(location='mock_loc', id=self.new_net.id))

    @patch.object(clc_common, 'find_network')
    @patch.object(ClcNetwork, '_update_network')
    @patch.object(ClcNetwork, '_create_network')
    def test_ensure_network_present_call_create(self,
                                                mock_create_network,
                                                mock_update_network,
                                                mock_find_network):
        mock_find_network.return_value = None
        location = 'mock_loc'
        search_key = 'mock_id'

        under_test = ClcNetwork(self.module)
        under_test._ensure_network_present(location, search_key)

        mock_create_network.assert_called_once_with(location)
        mock_update_network.assert_not_called()

    @patch.object(clc_common, 'find_network')
    @patch.object(ClcNetwork, '_update_network')
    @patch.object(ClcNetwork, '_create_network')
    def test_ensure_network_present_call_update(self,
                                                mock_create_network,
                                                mock_update_network,
                                                mock_find_network):
        mock_find_network.return_value = self.existing_net
        mock_update_network.return_value = (False, self.existing_net)
        location = 'mock_loc'
        search_key = 'mock_id'

        under_test = ClcNetwork(self.module)
        under_test.module.params = {
            'wait': True,
            'name': 'new_name'
        }

        under_test._ensure_network_present(location, search_key)

        mock_create_network.assert_not_called()
        mock_update_network.assert_called_once_with(location, self.existing_net)

    @patch.object(clc_common, 'find_network')
    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'Network')
    def test_ensure_network_present_no_change(self,
                                              mock_network,
                                              mock_call_api,
                                              mock_find_network):
        location = 'mock_loc'
        search_key = 'mock_id'
        network = mock.MagicMock()
        network.description = 'mock_desc'
        network.name = 'mock_name'

        mock_find_network.return_value = network

        under_test = ClcNetwork(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        under_test.module.params = {
            'wait': True,
            'description': network.description,
            'name': network.name,
        }
        changed, updated_network = under_test._ensure_network_present(
            location, search_key)

        self.assertFalse(changed)
        mock_call_api.assert_not_called()

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'Network')
    def test_update_network_exists_desc_different(self,
                                                  mock_network,
                                                  mock_call_api):
        location = 'mock_loc'
        network = mock.MagicMock()
        network.description = 'mock_desc'
        network.name = 'mock_name'

        under_test = ClcNetwork(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        under_test.module.params = {
            'wait': True,
            'description': 'new_desc',
            'name': network.name,
        }
        updated_network = under_test._update_network(location, network)

        mock_call_api.assert_called()

    @patch.object(clc_common, 'call_clc_api')
    @patch.object(clc_common, 'Network')
    def test_update_network_exists_name_different(self,
                                                  mock_network,
                                                  mock_call_api):
        location = 'mock_loc'
        network = mock.MagicMock()
        network.description = 'mock_desc'
        network.name = 'mock_name'

        under_test = ClcNetwork(self.module)
        under_test.clc_auth['clc_alias'] = 'mock_alias'
        under_test.module.params = {
            'wait': True,
            'description': network.description,
            'name': 'new_name',
        }
        updated_network = under_test._update_network(location, network)

        mock_call_api.assert_called()

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_network(self, mock_call_api):
        location = 'mock_loc'
        network = self.existing_net

        under_test = ClcNetwork(self.module)
        under_test.clc_auth['clc_alias'] = 'alias'
        under_test._delete_network(location, network)

        mock_call_api.assert_called_once_with(
            under_test.module, under_test.clc_auth, 'POST',
            '/networks/alias/mock_loc/{id}/release'.format(id=network.id))
        under_test.module.fail_json.assert_not_called()

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_network_exception(self, mock_call_api):
        location = 'mock_loc'
        network = self.existing_net

        error = ClcApiException('FAIL')
        mock_call_api.side_effect = [error]

        under_test = ClcNetwork(self.module)
        under_test.clc_auth['clc_alias'] = 'alias'
        under_test._delete_network(location, network)

        under_test.module.fail_json.assert_called_once_with(
            msg='Unable to release network: {id} in location: mock_loc. '
                'FAIL'.format(id=network.id))


if __name__ == '__main__':
    unittest.main()
