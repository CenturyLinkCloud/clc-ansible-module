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

import clc_ansible_module.clc_loadbalancer as clc_loadbalancer
from clc_ansible_module.clc_loadbalancer import ClcLoadBalancer

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import copy
import mock
from mock import patch
import unittest


class TestClcLoadbalancerFunctions(unittest.TestCase):

    def setUp(self):
        self.module = mock.MagicMock()
        self.clc_auth = {'clc_alias': 'mock_alias', 'clc_location': 'mock_dc'}

        self.loadbalancer_existing = {
            'id': 'mock_lb_id',
            'name': 'mock_name',
            'description': 'mock_desc',
            'status': 'enabled',
            'pools': []
        }
        self.pool_existing = {
            'id': 'mock_pool_id',
            'port': 80,
            'nodes': []
        }
        self.node_existing = {
            'ipAddress': '1.2.3.4',
            'privatePort': 80,
            'status': 'enabled'
        }
        self.node_modify = {
            'ipAddress': '5.6.7.8',
            'privatePort': 80,
            'status': 'enabled'
        }

        self.loadbalancer_new = {
            'id': 'new_lb_id',
            'name': 'new_name',
            'description': 'new_desc',
            'status': 'enabled',
            'pools': []
        }
        self.pool_new = {
            'id': 'new_pool_id',
            'port': 443,
            'nodes': []
        }
        self.node_new = {
            'ipAddress': '1.2.3.4',
            'privatePort': 443
        }

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'loadbalancer_list')
    @patch.object(ClcLoadBalancer, 'ensure_loadbalancer_present')
    def test_process_request_state_present(self,
                                           mock_loadbalancer_present,
                                           mock_loadbalancer_list,
                                           mock_authenticate):

        params = {
            'name': 'mock_name',
            'port': 80,
            'nodes': [self.node_existing],
            'state': 'present'
        }
        mock_authenticate.return_value = self.clc_auth
        loadbalancer_existing = self.loadbalancer_existing
        loadbalancer_existing['pools'].append(self.pool_existing)
        loadbalancer_existing['pools'][0]['nodes'].append(self.node_existing)
        mock_loadbalancer_list.return_value = [loadbalancer_existing]
        mock_loadbalancer_present.return_value = (False,
                                                  loadbalancer_existing)

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(
            changed=False, loadbalancer=loadbalancer_existing)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'loadbalancer_list')
    @patch.object(ClcLoadBalancer, 'ensure_loadbalancer_absent')
    def test_process_request_state_absent(self,
                                           mock_loadbalancer_absent,
                                           mock_loadbalancer_list,
                                           mock_authenticate):

        params = {
            'name': 'mock_name',
            'state': 'absent'
        }
        mock_authenticate.return_value = self.clc_auth
        mock_loadbalancer_list.return_value = [self.loadbalancer_existing]
        mock_loadbalancer_absent.return_value = (True, None)

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(
            changed=True, loadbalancer=None)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'loadbalancer_list')
    @patch.object(ClcLoadBalancer, 'ensure_pool_absent')
    def test_process_request_state_port_absent(self,
                                           mock_pool_absent,
                                           mock_loadbalancer_list,
                                           mock_authenticate):

        params = {
            'name': 'mock_name',
            'port': 80,
            'state': 'port_absent'
        }
        mock_authenticate.return_value = self.clc_auth
        loadbalancer_existing = self.loadbalancer_existing
        loadbalancer_existing['pools'].append(self.pool_existing)
        mock_loadbalancer_list.return_value = [loadbalancer_existing]
        mock_pool_absent.return_value = (
            True, self.loadbalancer_existing)

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(
            changed=True, loadbalancer=self.loadbalancer_existing)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'loadbalancer_list')
    @patch.object(ClcLoadBalancer, 'ensure_pool_nodes_present')
    def test_process_request_state_nodes_present(self,
                                                 mock_nodes_present,
                                                 mock_loadbalancer_list,
                                                 mock_authenticate):

        params = {
            'name': 'mock_name',
            'port': 80,
            'nodes': [self.node_existing],
            'state': 'nodes_present'
        }
        mock_authenticate.return_value = self.clc_auth
        loadbalancer_existing = self.loadbalancer_existing
        loadbalancer_existing['pools'].append(self.pool_existing)
        loadbalancer_existing['pools'][0]['nodes'].append(self.node_existing)
        mock_loadbalancer_list.return_value = [loadbalancer_existing]
        mock_nodes_present.return_value = (
            False, self.loadbalancer_existing)

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(
            changed=False, loadbalancer=loadbalancer_existing)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'loadbalancer_list')
    @patch.object(ClcLoadBalancer, 'ensure_pool_nodes_absent')
    def test_process_request_state_nodes_absent(self,
                                                mock_nodes_absent,
                                                mock_loadbalancer_list,
                                                mock_authenticate):

        params = {
            'name': 'mock_name',
            'port': 80,
            'nodes': [self.node_existing],
            'state': 'nodes_absent'
        }
        mock_authenticate.return_value = self.clc_auth
        loadbalancer_existing = self.loadbalancer_existing
        loadbalancer_existing['pools'].append(self.pool_existing)
        loadbalancer_result = loadbalancer_existing
        loadbalancer_existing['pools'][0]['nodes'].append(self.node_existing)
        mock_loadbalancer_list.return_value = [loadbalancer_existing]
        mock_nodes_absent.return_value = (
            True, loadbalancer_result)

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(
            changed=True, loadbalancer=loadbalancer_result)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    @patch.object(ClcLoadBalancer, 'create_loadbalancer')
    @patch.object(ClcLoadBalancer, 'update_loadbalancer')
    @patch.object(ClcLoadBalancer, 'ensure_pool_present')
    @patch.object(ClcLoadBalancer, 'ensure_pool_nodes_present')
    def test_ensure_loadbalancer_present_create(
            self, mock_nodes_present, mock_pool_present,
            mock_update_loadbalancer, mock_create_loadbalancer,
            mock_find_loadbalancer):
        params = {
            'name': 'new_name',
            'description': 'new_desc',
        }
        mock_find_loadbalancer.return_value = None
        mock_create_loadbalancer.return_value = self.loadbalancer_new

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, loadbalancer = under_test.ensure_loadbalancer_present()

        self.assertTrue(mock_create_loadbalancer.called)
        self.assertFalse(mock_update_loadbalancer.called)
        self.assertFalse(mock_pool_present.called)
        self.assertFalse(mock_nodes_present.called)

        self.assertTrue(changed)
        self.assertEqual(loadbalancer, self.loadbalancer_new)

    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    @patch.object(ClcLoadBalancer, 'create_loadbalancer')
    @patch.object(ClcLoadBalancer, 'update_loadbalancer')
    @patch.object(ClcLoadBalancer, 'ensure_pool_present')
    @patch.object(ClcLoadBalancer, 'ensure_pool_nodes_present')
    def test_ensure_loadbalancer_present_update(
            self, mock_nodes_present, mock_pool_present,
            mock_update_loadbalancer, mock_create_loadbalancer,
            mock_find_loadbalancer):
        params = {
            'name': 'mock_name',
            'description': 'updated_desc'
        }
        mock_find_loadbalancer.return_value = self.loadbalancer_existing
        loadbalancer_updated = self.loadbalancer_existing
        loadbalancer_updated['description'] = 'udpated_desc'

        mock_update_loadbalancer.return_value = loadbalancer_updated

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, loadbalancer = under_test.ensure_loadbalancer_present()

        self.assertFalse(mock_create_loadbalancer.called)
        self.assertTrue(mock_update_loadbalancer.called)
        self.assertFalse(mock_pool_present.called)
        self.assertFalse(mock_nodes_present.called)

        self.assertTrue(changed)
        self.assertEqual(loadbalancer, loadbalancer_updated)

    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    @patch.object(ClcLoadBalancer, 'create_loadbalancer')
    @patch.object(ClcLoadBalancer, 'update_loadbalancer')
    @patch.object(ClcLoadBalancer, 'ensure_pool_present')
    @patch.object(ClcLoadBalancer, 'ensure_pool_nodes_present')
    def test_ensure_loadbalancer_present_no_change(
            self, mock_nodes_present, mock_pool_present,
            mock_update_loadbalancer, mock_create_loadbalancer,
            mock_find_loadbalancer):
        params = {
            'name': 'mock_name',
            'description': 'mock_desc',
        }
        mock_find_loadbalancer.return_value = self.loadbalancer_existing

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, loadbalancer = under_test.ensure_loadbalancer_present()

        self.assertFalse(mock_create_loadbalancer.called)
        self.assertFalse(mock_update_loadbalancer.called)
        self.assertFalse(mock_pool_present.called)
        self.assertFalse(mock_nodes_present.called)

        self.assertFalse(changed)
        self.assertEqual(loadbalancer, self.loadbalancer_existing)

    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    @patch.object(ClcLoadBalancer, 'create_loadbalancer')
    @patch.object(ClcLoadBalancer, 'update_loadbalancer')
    @patch.object(ClcLoadBalancer, 'ensure_pool_present')
    @patch.object(ClcLoadBalancer, 'ensure_pool_nodes_present')
    def test_ensure_loadbalancer_present_add_nodes(
            self, mock_nodes_present, mock_pool_present,
            mock_update_loadbalancer, mock_create_loadbalancer,
            mock_find_loadbalancer):
        params = {
            'name': 'mock_name',
            'description': 'mock_desc',
            'port': 443,
            'nodes': [self.node_new]
        }
        loadbalancer_pool = copy.deepcopy(self.loadbalancer_existing)
        loadbalancer_pool['pools'].append(self.pool_new)
        loadbalancer_nodes = copy.deepcopy(loadbalancer_pool)
        loadbalancer_nodes['pools'][0]['nodes'].append(self.node_new)
        mock_find_loadbalancer.return_value = self.loadbalancer_existing
        mock_pool_present.return_value = (True, loadbalancer_pool)
        mock_nodes_present.return_value = (True, loadbalancer_nodes)

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, loadbalancer = under_test.ensure_loadbalancer_present()

        self.assertFalse(mock_create_loadbalancer.called)
        self.assertFalse(mock_update_loadbalancer.called)
        self.assertTrue(mock_pool_present.called)
        self.assertTrue(mock_nodes_present.called)

        self.assertTrue(changed)
        self.assertEqual(loadbalancer, loadbalancer_nodes)

    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    @patch.object(ClcLoadBalancer, 'delete_loadbalancer')
    def test_ensure_loadbalancer_absent(self, mock_delete_loadbalancer,
                                        mock_find_loadbalancer):
        mock_find_loadbalancer.return_value = self.loadbalancer_existing
        mock_delete_loadbalancer.return_value = None

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = {'name': 'mock_name'}

        changed, result = under_test.ensure_loadbalancer_absent()

        self.assertTrue(changed)
        self.assertIsNone(result)
        self.assertTrue(mock_delete_loadbalancer.called)

    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    @patch.object(ClcLoadBalancer, 'delete_loadbalancer')
    def test_ensure_loadbalancer_absent_no_change(self,
                                                  mock_delete_loadbalancer,
                                                  mock_find_loadbalancer):
        mock_find_loadbalancer.return_value = None

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = {'name': 'mock_name'}

        changed, loadbalancer = under_test.ensure_loadbalancer_absent()

        self.assertFalse(changed)
        self.assertIsNone(loadbalancer)
        self.assertFalse(mock_delete_loadbalancer.called)

    @patch.object(ClcLoadBalancer, '_find_pool')
    @patch.object(ClcLoadBalancer, 'create_pool')
    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    def test_ensure_pool_present_create(self, mock_find_loadbalancer,
                                        mock_create_pool, mock_find_pool):

        loadbalancer = copy.deepcopy(self.loadbalancer_existing)
        loadbalancer['pools'].append(self.pool_new)
        mock_find_pool.return_value = None
        mock_create_pool.return_value = self.pool_new
        mock_find_loadbalancer.return_value = loadbalancer

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False

        changed, result = under_test.ensure_pool_present(loadbalancer)

        self.assertTrue(changed)
        self.assertEqual(result, loadbalancer)
        self.assertTrue(mock_create_pool.called)

    @patch.object(ClcLoadBalancer, '_find_pool')
    @patch.object(ClcLoadBalancer, 'create_pool')
    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    def test_ensure_pool_present_no_change(self, mock_find_loadbalancer,
                                           mock_create_pool, mock_find_pool):

        loadbalancer = copy.deepcopy(self.loadbalancer_existing)
        loadbalancer['pools'].append(self.pool_existing)
        mock_find_pool.return_value = self.pool_existing

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False

        changed, result = under_test.ensure_pool_present(loadbalancer)

        self.assertFalse(changed)
        self.assertEqual(result, loadbalancer)
        self.assertFalse(mock_create_pool.called)

    @patch.object(ClcLoadBalancer, '_find_pool')
    @patch.object(ClcLoadBalancer, 'delete_pool')
    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    def test_ensure_pool_absent_delete(self, mock_find_loadbalancer,
                                       mock_delete_pool, mock_find_pool):
        loadbalancer = copy.deepcopy(self.loadbalancer_existing)
        loadbalancer['pools'].append(self.pool_existing)
        mock_find_loadbalancer.side_effect = [loadbalancer,
                                              self.loadbalancer_existing]
        mock_find_pool.return_value = self.pool_existing
        mock_delete_pool.return_value = None

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = {'name': 'mock_name'}

        changed, result = under_test.ensure_pool_absent()

        self.assertTrue(changed)
        self.assertEqual(result, self.loadbalancer_existing)
        self.assertTrue(mock_delete_pool.called)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcLoadBalancer, '_find_pool')
    @patch.object(ClcLoadBalancer, 'delete_pool')
    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    def test_ensure_pool_absent_error(self, mock_find_loadbalancer,
                                      mock_delete_pool, mock_find_pool):
        mock_find_loadbalancer.side_effect = [None, None]

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = {'name': 'mock_name'}

        under_test.ensure_pool_absent()

        self.module.fail_json.assert_called_once_with(
            msg='No load balancers matching: mock_name.')

    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    @patch.object(ClcLoadBalancer, '_find_pool')
    @patch.object(ClcLoadBalancer, 'create_pool')
    @patch.object(ClcLoadBalancer, '_update_node_list')
    @patch.object(ClcLoadBalancer, '_update_pool_nodes')
    def test_ensure_pool_nodes_present_add(
            self, mock_update_nodes, mock_node_list, mock_create_pool,
            mock_find_pool, mock_find_loadbalancer):
        params = {
            'name': 'mock_name',
            'port': 443,
            'nodes': [self.node_new]
        }
        loadbalancer = copy.deepcopy(self.loadbalancer_existing)
        loadbalancer['pools'].append(copy.deepcopy(self.pool_new))
        loadbalancer['pools'][0]['nodes'].append(self.node_new)
        mock_find_loadbalancer.side_effect = [self.loadbalancer_existing,
                                              loadbalancer]
        mock_find_pool.return_value = None
        mock_create_pool.return_value = self.pool_new
        mock_node_list.return_value = [self.node_new]
        mock_update_nodes.return_value = [self.node_new]

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, result = under_test.ensure_pool_nodes_present()

        self.assertTrue(changed)
        self.assertEqual(result, loadbalancer)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    @patch.object(ClcLoadBalancer, '_find_pool')
    @patch.object(ClcLoadBalancer, 'create_pool')
    @patch.object(ClcLoadBalancer, '_update_node_list')
    @patch.object(ClcLoadBalancer, '_update_pool_nodes')
    def test_ensure_pool_nodes_present_not_found(
            self, mock_update_nodes, mock_node_list, mock_create_pool,
            mock_find_pool, mock_find_loadbalancer):
        params = {
            'name': 'mock_name',
            'port': 443,
            'nodes': [self.node_new]
        }
        mock_find_loadbalancer.side_effect = [None, None]

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        under_test.ensure_pool_nodes_present()

        self.module.fail_json.assert_called_once_with(
            msg='No load balancers matching: mock_name.')

    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    @patch.object(ClcLoadBalancer, '_find_pool')
    @patch.object(ClcLoadBalancer, '_update_node_list')
    @patch.object(ClcLoadBalancer, '_update_pool_nodes')
    def test_ensure_pool_nodes_absent_remove(
            self, mock_update_nodes, mock_node_list,
            mock_find_pool, mock_find_loadbalancer):
        params = {
            'name': 'mock_name',
            'port': 443,
            'nodes': [self.node_existing]
        }
        loadbalancer = copy.deepcopy(self.loadbalancer_existing)
        loadbalancer['pools'].append(copy.deepcopy(self.pool_existing))
        loadbalancer_changed = copy.deepcopy(loadbalancer)
        loadbalancer['pools'][0]['nodes'].append(self.node_existing)
        mock_find_loadbalancer.side_effect = [loadbalancer,
                                              loadbalancer_changed]
        pool = self.pool_existing.copy()
        pool['nodes'].append(self.node_existing)
        mock_find_pool.return_value = pool
        mock_node_list.return_value = []
        mock_update_nodes.return_value = self.pool_existing

        under_test = ClcLoadBalancer(self.module)
        under_test.module.check_mode = False
        under_test.module.params = params

        changed, result = under_test.ensure_pool_nodes_absent()

        self.assertTrue(changed)
        self.assertEqual(result, loadbalancer_changed)
        self.assertFalse(self.module.fail_json.called)


    @patch.object(ClcLoadBalancer, '_find_loadbalancer')
    @patch.object(ClcLoadBalancer, '_find_pool')
    @patch.object(ClcLoadBalancer, '_update_node_list')
    @patch.object(ClcLoadBalancer, '_update_pool_nodes')
    def test_ensure_pool_nodes_absent_not_found(
                self, mock_update_nodes, mock_node_list,
                mock_find_pool, mock_find_loadbalancer):
            params = {
                'name': 'mock_name',
                'port': 443,
                'nodes': [self.node_new]
            }
            mock_find_loadbalancer.side_effect = [None, None]

            under_test = ClcLoadBalancer(self.module)
            under_test.module.check_mode = False
            under_test.module.params = params

            under_test.ensure_pool_nodes_absent()

            self.module.fail_json.assert_called_once_with(
                msg='No load balancers matching: mock_name.')

    @patch.object(clc_common, 'server_ids_in_datacenter')
    @patch.object(clc_common, 'call_clc_api')
    def test_create_loadbalancer(self, mock_call_api, mock_server_ids):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
            'name': 'new_name'
        }
        mock_server_ids.return_value = ['mock_id1', 'mock_id2']
        mock_call_api.return_value = self.loadbalancer_new

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.create_loadbalancer()

        self.assertEqual(result, self.loadbalancer_new)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'server_ids_in_datacenter')
    @patch.object(clc_common, 'call_clc_api')
    def test_create_loadbalancer_exception_no_servers(self, mock_call_api,
                                                      mock_server_ids):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
            'name': 'new_name'
        }
        mock_server_ids.return_value = []

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.create_loadbalancer()

        self.module.fail_json.assert_called_with(
            msg='Cannot create load balancer for account: mock_alias '
                'in location: mock_dc. No servers are present in datacenter.')

    @patch.object(clc_common, 'server_ids_in_datacenter')
    @patch.object(clc_common, 'call_clc_api')
    def test_create_loadbalancer_exception(self, mock_call_api,
                                           mock_server_ids):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
            'name': 'new_name'
        }
        mock_server_ids.return_value = ['mock_id1', 'mock_id2']
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.create_loadbalancer()

        self.module.fail_json.assert_called_with(
            msg='Unable to create load balancer with name: new_name '
                'for account: mock_alias in location: mock_dc. Failed')

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_loadbalancer(self, mock_call_api):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
        }
        mock_call_api.return_value = None

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.delete_loadbalancer(self.loadbalancer_existing)

        self.assertIsNone(result)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_loadbalancer_exception(self, mock_call_api):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
        }
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.delete_loadbalancer(self.loadbalancer_existing)

        self.module.fail_json.assert_called_with(
            msg='Unable to delete load balancer with name: mock_name. Failed')

    @patch.object(clc_common, 'call_clc_api')
    def test_update_loadbalancer(self, mock_call_api):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
            'name': 'new_name',
            'description': 'new_desc'
        }
        mock_call_api.return_value = self.loadbalancer_new

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.update_loadbalancer(self.loadbalancer_existing)

        self.assertEqual(result, self.loadbalancer_new)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_update_loadbalancer_exception(self, mock_call_api):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
            'name': 'mock_name',
            'description': 'mock_desc'
        }
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.update_loadbalancer(self.loadbalancer_existing)

        self.module.fail_json.assert_called_with(
            msg='Unable to update load balancer with name: mock_name. Failed')

    @patch.object(clc_common, 'call_clc_api')
    def test_create_pool(self, mock_call_api):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
        }
        mock_call_api.return_value = self.pool_new

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.create_pool(self.loadbalancer_existing)

        self.assertEqual(result, self.pool_new)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_create_pool_exception(self, mock_call_api):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
        }
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.create_pool(self.loadbalancer_existing)

        self.module.fail_json.assert_called_with(
            msg='Unable to create pool for load balancer with '
                'name: mock_name. Failed')

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_pool(self, mock_call_api):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
        }
        mock_call_api.return_value = None

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.delete_pool(self.loadbalancer_existing,
                                        self.pool_existing)

        self.assertIsNone(result)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_delete_pool_exception(self, mock_call_api):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
        }
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test.delete_pool(self.loadbalancer_existing,
                                        self.pool_existing)

        self.module.fail_json.assert_called_once_with(
            msg='Unable to delete pool on port: {port} for load balancer '
                'with name: {name}. Failed'.format(
                    port=self.pool_existing['port'],
                    name=self.loadbalancer_existing['name']))

    @patch.object(clc_common, 'call_clc_api')
    def test_update_pool_nodes(self, mock_call_api):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
        }
        mock_call_api.return_value = None

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test._update_pool_nodes(self.loadbalancer_existing,
                                               self.pool_existing,
                                               [self.node_new])

        self.assertIsNone(result)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'call_clc_api')
    def test_update_pool_nodes_exception(self, mock_call_api):
        params = {
            'alias': 'mock_alias',
            'location': 'mock_dc',
        }
        error = ClcApiException('Failed')
        mock_call_api.side_effect = error

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test._update_pool_nodes(self.loadbalancer_existing,
                                               self.pool_existing,
                                               [self.node_new])

        self.module.fail_json.assert_called_once_with(
            msg='Unable to updated nodes in pool on port: {port} '
                'for load balancer with name: {name}. Failed'.format(
                    port=self.pool_existing['port'],
                    name=self.loadbalancer_existing['name']))

    @patch.object(clc_common, 'loadbalancer_list')
    def test_find_loadbalancer(self, mock_loadbalancer_list):
        mock_loadbalancer_list.return_value = [self.loadbalancer_existing]
        under_test = ClcLoadBalancer(self.module)

        result = under_test._find_loadbalancer(
            self.loadbalancer_existing['id'], refresh=True)

        self.assertEqual(result, self.loadbalancer_existing)

    def test_find_pool(self):
        loadbalancer = self.loadbalancer_existing
        loadbalancer['pools'].append(self.pool_existing)

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = {'port': self.pool_existing['port']}

        result = under_test._find_pool(loadbalancer)

        self.assertEqual(result, self.pool_existing)

    def test_update_node_list_add(self):
        existing_nodes = [self.node_existing]
        params = {'nodes': [self.node_modify]}

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test._update_node_list(existing_nodes)

        self.assertEqual(result,
                         [self.node_existing, self.node_modify])

    def test_update_node_list_remove(self):
        existing_nodes = [self.node_existing, self.node_modify]
        params = {'nodes': [self.node_modify]}

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test._update_node_list(existing_nodes, remove_nodes=True)

        self.assertEqual(result, [self.node_existing])

    def test_update_node_list_no_change(self):
        existing_nodes = [self.node_existing]
        params = {'nodes': [self.node_existing]}

        under_test = ClcLoadBalancer(self.module)
        under_test.module.params = params

        result = under_test._update_node_list(existing_nodes)

        self.assertEqual(result, [self.node_existing])

    @patch.object(clc_loadbalancer, 'AnsibleModule')
    @patch.object(clc_loadbalancer, 'ClcLoadBalancer')
    def test_main(self, mock_ClcLoadBalancer, mock_AnsibleModule):
        mock_ClcLoadBalancer_instance          = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcLoadBalancer.return_value      = mock_ClcLoadBalancer_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_loadbalancer.main()

        mock_ClcLoadBalancer.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcLoadBalancer_instance.process_request.call_count == 1

if __name__ == '__main__':
    unittest.main()
