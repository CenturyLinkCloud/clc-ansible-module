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
from clc import APIFailedResponse
import mock
from mock import patch
import unittest

class TestClcLoadbalancerFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter=mock.MagicMock()

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__

        def mock_import(name, *args):
            if name == 'clc':
                raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_loadbalancer)
            ClcLoadBalancer(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(
            msg='clc-python-sdk required for this module')

        # Reset
        reload(clc_loadbalancer)

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
            reload(clc_loadbalancer)
            ClcLoadBalancer(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library  version should be >= 2.5.0')

        # Reset
        reload(clc_loadbalancer)

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
            reload(clc_loadbalancer)
            ClcLoadBalancer(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library is required for this module')

        # Reset
        reload(clc_loadbalancer)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_set_clc_credentials_from_env')
    def test_process_request_state_present(self,
                                           mock_set_clc_credentials,
                                           mock_clc_sdk):

        # Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 80 }],
            'state': 'present'
        }
        mock_loadbalancer_response = [{'name': 'TEST_LB'}]

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'name': 'test'}],
            {'id': 'test', 'name': 'test'},
            [],
            {'id': 'test', 'name': 'test'},
            []
        ]
        # TODO: Mock a response to API.Call('POST')
        self.module.check_mode = False
        # Under Test
        under_test = ClcLoadBalancer(self.module)
        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(changed=False, loadbalancer = {'id': 'test', 'name': 'test'})
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_set_user_agent(self, mock_clc_sdk):
        clc_loadbalancer.__version__ = "1"
        ClcLoadBalancer._set_user_agent(mock_clc_sdk)

        self.assertTrue(mock_clc_sdk.SetRequestsSession.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_set_clc_credentials_from_env')
    def test_process_request_state_absent(self,
                                          mock_set_clc_credentials,
                                          mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'state': 'absent'
        }
        mock_loadbalancer_response = [{'name': 'test', 'id': 'test'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_loadbalancer_response
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        test.process_request()

        #Assertions
        self.module.exit_json.assert_called_once_with(changed=True, loadbalancer=[{'name': 'test', 'id': 'test'}])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_set_clc_credentials_from_env')
    def test_process_request_state_port_absent(self,
                                          mock_set_clc_credentials,
                                          mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'state': 'port_absent'
        }

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test', 'name': 'test'}],
            [{'port': '80', 'id':'test'}],
            {}
        ]
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        test.process_request()

        #Assertions
        self.module.exit_json.assert_called_once_with(changed=True, loadbalancer={})
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_set_clc_credentials_from_env')
    def test_process_request_state_nodes_present(self,
                                          mock_set_clc_credentials,
                                          mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }],
            'state': 'nodes_present'
        }

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test', 'name': 'test'}],
            [{'port': '80', 'id':'test'}],
            [{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }]
        ]

        test = ClcLoadBalancer(self.module)
        test.process_request()

        #Assertions
        self.module.exit_json.assert_called_once_with(changed=False, loadbalancer={})
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_set_clc_credentials_from_env')
    def test_process_request_state_nodes_present_no_lb(self,
                                          mock_set_clc_credentials,
                                          mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }],
            'state': 'nodes_present'
        }

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test1', 'name': 'test1'}],
            [{'port': '80', 'id':'test'}],
            [{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }]
        ]

        test = ClcLoadBalancer(self.module)
        test.process_request()

        #Assertions
        self.module.exit_json.assert_called_once_with(changed=False, loadbalancer='Load balancer doesn\'t Exist')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_set_clc_credentials_from_env')
    def test_process_request_state_nodes_present_no_pool(self,
                                          mock_set_clc_credentials,
                                          mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }],
            'state': 'nodes_present'
        }

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test', 'name': 'test'}],
            [{'port': '81', 'id':'test'}],
            [{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }]
        ]

        test = ClcLoadBalancer(self.module)
        test.process_request()

        #Assertions
        self.module.exit_json.assert_called_once_with(changed=False, loadbalancer='Pool doesn\'t exist')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_set_clc_credentials_from_env')
    def test_process_request_state_nodes_absent_no_lb(self,
                                          mock_set_clc_credentials,
                                          mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 80 }],
            'state': 'nodes_absent'
        }

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test1', 'name': 'test1'}],
            [{'port': '80', 'id':'test'}],
            [{ 'ipAddress': '10.82.152.15', 'privatePort': 80}]
        ]

        test = ClcLoadBalancer(self.module)
        test.process_request()

        #Assertions
        self.module.exit_json.assert_called_once_with(changed=False, loadbalancer='Load balancer doesn\'t Exist')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_set_clc_credentials_from_env')
    def test_process_request_state_nodes_absent_no_pool(self,
                                          mock_set_clc_credentials,
                                          mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }],
            'state': 'nodes_absent'
        }

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test', 'name': 'test'}],
            [{'port': '81', 'id':'test'}],
            [{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }]
        ]

        test = ClcLoadBalancer(self.module)
        test.process_request()

        #Assertions
        self.module.exit_json.assert_called_once_with(changed=False, loadbalancer='Pool doesn\'t exist')
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_set_clc_credentials_from_env')
    def test_process_request_state_nodes_absent(self,
                                          mock_set_clc_credentials,
                                          mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 82, 'status': 'enabled' }],
            'state': 'nodes_absent'
        }

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test', 'name': 'test'}],
            [{'port': '80', 'id':'test'}],
            [{ 'ipAddress': '10.82.152.15', 'privatePort': 81, 'status': 'enabled' }]
        ]

        test = ClcLoadBalancer(self.module)
        test.process_request()

        #Assertions
        self.module.exit_json.assert_called_once_with(changed=False, loadbalancer={})
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_get_lbpool_nodes')
    @patch.object(ClcLoadBalancer, 'set_loadbalancernodes')
    def test_add_lbpool_nodes(self, mock_set_pool_nodes, mock_get_pool_nodes, mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 82, 'status': 'enabled' }],
            'state': 'nodes_absent'
        }
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        mock_get_pool_nodes.return_value = [{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }]
        mock_set_pool_nodes.return_value = 'success'
        result = test.add_lbpool_nodes('alias','location','lb_id','pool_id',
                                       [{'ipAddress': '1.1.1.1', 'privatePort': 80}])
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(result, (True, 'success'))

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_get_lbpool_nodes')
    @patch.object(ClcLoadBalancer, 'set_loadbalancernodes')
    def test_remove_lbpool_nodes(self, mock_set_pool_nodes, mock_get_pool_nodes, mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }],
            'state': 'nodes_absent'
        }
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        mock_get_pool_nodes.return_value = [{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }]
        mock_set_pool_nodes.return_value = 'success'
        result = test.remove_lbpool_nodes('alias','location','lb_id','pool_id',
                                       [{ 'ipAddress': '10.82.152.15', 'privatePort': 80}])
        self.assertFalse(self.module.fail_json.called)
        self.assertEqual(result, (True, 'success'))

    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_set_loadbalancernodes_pool_id(self, mock_clc_sdk):

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test', 'name': 'test'}],
            [{'port': '80', 'id':'test'}],
            [{ 'ipAddress': '10.82.152.15', 'privatePort': 81, 'status': 'enabled' }]
        ]
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        result = test.set_loadbalancernodes('alias', 'location', 'lb_id', 'pool_id', [1,2,3])
        self.assertIsNotNone(result)
        self.assertEqual(result[0].get('id'), 'test')

    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_set_loadbalancernodes_lb_id_none(self, mock_clc_sdk):

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test', 'name': 'test'}],
            [{'port': '80', 'id':'test'}],
            [{ 'ipAddress': '10.82.152.15', 'privatePort': 81, 'status': 'enabled' }]
        ]
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        result = test.set_loadbalancernodes('alias', 'location', None, 'pool_id', [1,2,3])
        self.assertIsNone(result)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_create_loadbalancer_exception(self, mock_clc_sdk):
        error = APIFailedResponse('Failed')
        error.response_text = 'Mock failure response'
        mock_clc_sdk.v2.API.Call.side_effect = error
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        result = test.create_loadbalancer('name', 'alias', 'location', 'description', 'status')
        self.module.fail_json.assert_called_with(msg='Unable to create load balancer "name". Mock failure response')

    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_create_loadbalancerpool_exception(self, mock_clc_sdk):
        error = APIFailedResponse('Failed')
        error.response_text = 'Mock failure response'
        mock_clc_sdk.v2.API.Call.side_effect = error
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        result = test.create_loadbalancerpool('alias', 'location', 'lb_id', 'method', 'persistance', 'port')
        self.module.fail_json.assert_called_with(msg='Unable to create pool for load balancer id "lb_id". Mock failure response')

    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_delete_loadbalancerpool_exception(self, mock_clc_sdk):
        error = APIFailedResponse('Failed')
        error.response_text = 'Mock failure response'
        mock_clc_sdk.v2.API.Call.side_effect = error
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        result = test.delete_loadbalancerpool('alias', 'location', 'lb_id', 'pool_id')
        self.module.fail_json.assert_called_with(msg='Unable to delete pool for load balancer id "lb_id". Mock failure response')

    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_set_loadbalancernodes_exception(self, mock_clc_sdk):
        error = APIFailedResponse('Failed')
        error.response_text = 'Mock failure response'
        mock_clc_sdk.v2.API.Call.side_effect = error
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        result = test.set_loadbalancernodes('alias', 'location', 'lb_id', 'pool_id', [1,2,3])
        self.module.fail_json.assert_called_with(msg='Unable to set nodes for the load balancer pool id "pool_id". Mock failure response')

    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_get_loadbalancer_list_exception(self, mock_clc_sdk):
        error = APIFailedResponse('Failed')
        error.response_text = 'Mock failure response'
        mock_clc_sdk.v2.API.Call.side_effect = error
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        test._get_loadbalancer_list('alias', 'location')
        self.module.fail_json.assert_called_with(msg='Unable to fetch load balancers for account: alias. Mock failure response')

    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_loadbalancerpool_exists_exception(self, mock_clc_sdk):
        error = APIFailedResponse('Failed')
        error.response_text = 'Mock failure response'
        mock_clc_sdk.v2.API.Call.side_effect = error
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        test._loadbalancerpool_exists('alias', 'location', 90, 'lb_id')
        self.module.fail_json.assert_called_with(msg='Unable to fetch the load balancer pools for for load balancer id: lb_id. Mock failure response')

    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_get_lbpool_nodes_exception(self, mock_clc_sdk):
        error = APIFailedResponse('Failed')
        error.response_text = 'Mock failure response'
        mock_clc_sdk.v2.API.Call.side_effect = error
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        result = test._get_lbpool_nodes('alias', 'location', 'lb_id', 'pool_id')
        self.module.fail_json.assert_called_with(msg='Unable to fetch list of available nodes for load balancer pool id: pool_id. Mock failure response')
        self.assertEqual(result, None)

    @patch.object(ClcLoadBalancer, '_get_loadbalancer_id')
    @patch.object(clc_loadbalancer, 'clc_sdk')
    def test_delete_loadbalancer_exception(self, mock_clc_sdk, mock_get):
        error = APIFailedResponse('Failed')
        error.response_text = 'Mock failure response'
        mock_clc_sdk.v2.API.Call.side_effect = error
        mock_get.return_value = 'lb_id'
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        result = test.delete_loadbalancer('alias', 'location', 'name')
        self.module.fail_json.assert_called_with(msg='Unable to delete load balancer "name". Mock failure response')

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_get_lbpool_nodes')
    def test_loadbalancerpool_nodes_exists_true(self, mock_get_pool_nodes, mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }],
            'state': 'nodes_absent'
        }
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        mock_get_pool_nodes.return_value = [{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }]
        result = test._loadbalancerpool_nodes_exists('alias','location','lb_id','pool_id',
                                       [{ 'ipAddress': '10.82.152.15', 'privatePort': 80}])
        self.assertEqual(result, True)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_get_lbpool_nodes')
    def test_loadbalancerpool_nodes_exists_false(self, mock_get_pool_nodes, mock_clc_sdk):
        #Setup
        self.module.params = {
            'name': 'test',
            'port': 80,
            'nodes':[{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }],
            'state': 'nodes_absent'
        }
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        mock_get_pool_nodes.return_value = [{ 'ipAddress': '10.82.152.15', 'privatePort': 80, 'status': 'enabled' }]
        result = test._loadbalancerpool_nodes_exists('alias','location','lb_id','pool_id',
                                       [{ 'ipAddress': '10.82.152.15', 'privatePort': 90}])
        self.assertEqual(result, False)

    def test_ensure_loadbalancerpool_present_no_lb_id(self):
        under_test = ClcLoadBalancer(self.module)
        changed, result, pool_id = under_test.ensure_loadbalancerpool_present(
            None, 'alias', 'location', 'method', 'persistence', 'port')
        self.assertEqual(changed, False)
        self.assertEqual(result, None)
        self.assertEqual(pool_id, None)

    @patch.object(ClcLoadBalancer, '_loadbalancer_exists')
    def test_ensure_loadbalancerpool_absent_no_lb(self, mock_lb_exists):
        mock_lb_exists.return_value = False
        under_test = ClcLoadBalancer(self.module)
        changed, result = under_test.ensure_loadbalancerpool_absent('alias', 'location', 'name', 'port')
        self.assertEqual(changed, False)
        self.assertEqual(result, 'LB Doesn\'t Exist')

    @patch.object(ClcLoadBalancer, '_loadbalancerpool_exists')
    @patch.object(ClcLoadBalancer, '_get_loadbalancer_id')
    @patch.object(ClcLoadBalancer, '_loadbalancer_exists')
    def test_ensure_loadbalancerpool_absent_no_lb_pool(self, mock_lb_exists, mock_get_lb, mock_lb_pool_exists):
        mock_lb_exists.return_value = True
        mock_get_lb.return_value = 'lb name'
        mock_lb_pool_exists.return_value = False
        under_test = ClcLoadBalancer(self.module)
        changed, result = under_test.ensure_loadbalancerpool_absent('alias', 'location', 'name', 'port')
        self.assertEqual(changed, False)
        self.assertEqual(result, 'Pool doesn\'t exist')

    @patch.object(ClcLoadBalancer, '_loadbalancerpool_exists')
    @patch.object(ClcLoadBalancer, '_get_loadbalancer_id')
    @patch.object(ClcLoadBalancer, '_loadbalancer_exists')
    def test_ensure_lbpool_nodes_set_no_lb_pool(self, mock_lb_exists, mock_get_lb, mock_lb_pool_exists):
        mock_lb_exists.return_value = True
        mock_get_lb.return_value = 'lb name'
        mock_lb_pool_exists.return_value = False
        under_test = ClcLoadBalancer(self.module)
        changed, result = under_test.ensure_lbpool_nodes_set('alias', 'location', 'name', 'port', [1,2,3])
        self.assertEqual(changed, False)
        self.assertEqual(result, 'Pool doesn\'t exist')

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, '_loadbalancer_exists')
    @patch.object(ClcLoadBalancer, '_get_loadbalancer_id')
    @patch.object(ClcLoadBalancer, '_loadbalancerpool_exists')
    @patch.object(ClcLoadBalancer, '_loadbalancerpool_nodes_exists')
    @patch.object(ClcLoadBalancer, 'set_loadbalancernodes')
    def test_ensure_lbpool_nodes_set(self, set_lb_nodes, lbpool_nodes_exists, lbpool_exists, get_lb_id, lb_exists, mock_clc_sdk):
        lb_exists.return_value = True
        get_lb_id.return_value = '123'
        lbpool_exists.retrun_value = True
        lbpool_nodes_exists.return_value = False
        set_lb_nodes.return_value = 'success'
        self.module.check_mode = False
        test = ClcLoadBalancer(self.module)
        result = test.ensure_lbpool_nodes_set('alias', 'location', 'name', 80, [1,2,3])
        self.assertEqual(result, (True, 'success'))

    @patch.object(ClcLoadBalancer, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            under_test = ClcLoadBalancer(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcLoadBalancer, 'clc')
    def test_set_clc_credentials_w_api_url(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_URL': 'dummyapiurl'}):
            under_test = ClcLoadBalancer(self.module)
            under_test._set_clc_credentials_from_env()
            self.assertEqual(under_test.clc.defaults.ENDPOINT_URL_V2, 'dummyapiurl')


    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcLoadBalancer(self.module)
            under_test._set_clc_credentials_from_env()

        self.assertEqual(self.module.fail_json.called, True)

    def test_define_argument_spec(self):
        result = ClcLoadBalancer.define_argument_spec()
        self.assertIsInstance(result, dict)

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
