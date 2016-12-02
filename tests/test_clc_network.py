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
import clc as clc_sdk
from clc import CLCException

def FakeAnsibleModule():
    module = mock.MagicMock()
    module.check_mode = False
    module.params = {}
    return module

class TestClcNetwork(unittest.TestCase):

    def setUp(self):

        existing_net = mock.MagicMock()
        existing_net.name = 'existing'
        existing_net.data = {'name': 'existing'}
        self.mock_nets = [existing_net]
        self.existing_net = existing_net

        new_net = mock.MagicMock()
        new_net.name = 'new'
        new_net.data = {'name': 'new'}
        self.new_net = new_net

        self.module = FakeAnsibleModule()
        self.network = ClcNetwork(self.module)
        self.network.module.exit_json = mock.MagicMock()
        self.network.api = mock.MagicMock()
        self.network_dict = {}
        self.network.clc.v2.Network  = mock.MagicMock()
        self.network.clc.v2.Networks = mock.MagicMock()
        self.network.clc.v2.API.Call = mock.MagicMock()

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        real_import = __import__
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
            id=dict(required=False),
            name=dict(required=False),
            location=dict(required=True),
            description=dict(required=False),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(default=True, type='bool')
        ))

    @patch.object(clc_common, 'authenticate')
    @patch.object(ClcNetwork, '_populate_networks')
    @patch.object(ClcNetwork, '_ensure_network_present')
    def test_process_request_populates_network_present(self,
                                                       mock_network_present,
                                                       mock_populate_networks,
                                                       mock_authenticate):
        params = {
            'id': 'nope',
            'location': 'mock_loc'
        }
        under_test = ClcNetwork(self.module)
        under_test.module.params = params
        mock_populate_networks.return_value = self.mock_nets
        mock_network_present.return_value = (True, self.new_net)
        under_test.process_request()

        # Assert
        mock_populate_networks.assert_called_once_with('mock_loc')
        mock_network_present.assert_called_once_with(params)

    @patch.object(clc_common, 'authenticate')
    @patch.object(ClcNetwork, '_populate_networks')
    @patch.object(ClcNetwork, '_ensure_network_absent')
    def test_process_request_populates_network_absent(self,
                                                      mock_network_absent,
                                                      mock_populate_networks,
                                                      mock_authenticate):
        params = {
            'id': 'nope',
            'state': 'absent',
            'location': 'mock_loc'
        }
        under_test = ClcNetwork(self.module)
        under_test.module.params = params
        mock_populate_networks.return_value = self.mock_nets
        mock_network_absent.return_value = (False, self.mock_nets)
        under_test.process_request()

        # Assert
        mock_populate_networks.assert_called_once_with('mock_loc')
        mock_network_absent.assert_called_once_with(params)

    def test_process_request_present_waits_on_request(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            mock_request = mock.MagicMock()
            mock_request.WaitUntilComplete = mock.MagicMock(return_value=0)
            self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_request)
            self.module.params = {
                'location': 'mock_loc'
            }

            self.network.process_request()

            self.assertEqual(1, mock_request.WaitUntilComplete.call_count)
            self.assertEqual(self.module.fail_json.called, False)

    def ugly_setup(self, mock_update, network_id):
        """
        Long comment time!  This level of setup is most certainly unnecessary, as this
        logic should be handled in the Python SDK.  Unfortunately, since the network API
        remains in the 'experimental' space, it stands to reason that it will be further
        refined/changed, so effort is not being expended enhacing the Requests portion of
        the SDK to handle waiting on and returning network objects post-wait.  As a stop-gap,
        enjoy the mocking shenanigans that follow.
        """

        # Step the first: Mock the status request
        initial_name = 'vlan_bob_192.168.222'
        initial_desc = 'vlan_bob_192.168.222 description'
        status_uri = '/v2-experimental/operations/xxx/status/id'
        network_uri = '/v2-experimental/networks/xxx/dcx/54321'

        mock_request = mock.MagicMock()
        mock_request.uri = status_uri
        status_output = {
            'requestType': 'blueprintOperation',
            'status': 'succeeded',
            'summary': {
                'blueprintId': 12345,
                'locationId': 'DCx',
                'links': [{
                    'href': network_uri,
                    'id': network_id,
                    'rel': 'network'
                }]
            }
        }

        # Step the Second: Mock out the two API calls
        new_network = {
            'name': initial_name,
            'links': [],
            'vlan': 'bob',
            'id': network_id,
            'netmask': '255.255.255.0',
            'cidr': '192.168.222.0/24',
            'type': 'private',
            'gateway': '192.168.222.1',
            'description': initial_desc
        }

        response_map = {
            status_uri: status_output,
            network_uri: new_network
        }

        self.network.clc.v2.API.Call = mock.MagicMock(side_effect=lambda x, uri: response_map[uri] if uri in response_map else 'doing it wrong')

        # Step the Third: Mock the instantiation of a v2 Network object
        mock_network = mock.MagicMock()
        mock_network.id = network_id
        mock_network.name = initial_name
        mock_network.data = new_network
        self.network.clc.v2.Network = mock.MagicMock(return_value=mock_network)

        # Step the Fourth: Mock the wait/create calls
        mock_requests = mock.MagicMock()
        mock_requests.requests = [mock_request]
        mock_requests.WaitUntilComplete = mock.MagicMock(return_value=0)
        self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_requests)
        mock_update.return_value = True, mock_network

        return status_uri, network_uri, mock_network

    @patch.object(ClcNetwork, '_update_network')
    def test_process_request_present_updates_network_after_create_wait_if_provided_name_or_desc(self, mock_update):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            network_id = 24601
            uri1, uri2, mock_network = self.ugly_setup(mock_update, network_id)
            new_name = "mocketymockmock"
            new_desc = "mockerymockmockdesc"
            self.module.params = {
                'name': new_name,
                'desc': new_desc,
                'location': 'mock_loc'
            }
            self.network.process_request()

            self.assertEqual(2, self.network.clc.v2.API.Call.call_count)
            self.network.clc.v2.API.Call.assert_any_call('GET', uri1)
            self.network.clc.v2.API.Call.assert_called_with('GET', uri2)
            self.network.clc.v2.Network.assert_called_once_with(network_id,network_obj=mock_network.data)
            mock_update.assert_called_once_with(mock_network,self.module.params)

    @patch.object(ClcNetwork, '_update_network')
    def test_process_request_present_skips_update_after_create_if_no_name_or_desc_are_provided(self, mock_update):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            network_id = 24601
            uri1, uri2, mock_network = self.ugly_setup(mock_update, network_id)
            new_name = "mocketymockmock"
            new_desc = "mockerymockmockdesc"
            self.module.params = {
                'location': 'mock_loc'
            }
            self.network.process_request()

            self.assertEqual(2, self.network.clc.v2.API.Call.call_count)
            self.network.clc.v2.API.Call.assert_any_call('GET', uri1)
            self.network.clc.v2.API.Call.assert_called_with('GET', uri2)
            self.network.clc.v2.Network.assert_called_once_with(network_id,network_obj=mock_network.data)
            mock_update.assert_not_called()


    def test_process_request_present_reports_failure_when_create_fails(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            mock_request = mock.MagicMock()
            mock_request.WaitUntilComplete = mock.MagicMock(return_value=1)
            self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_request)
            self.module.params = {
                'location': 'mock_loc'
            }

            self.network.process_request()

            self.assertEqual(1, mock_request.WaitUntilComplete.call_count)
            self.module.fail_json.assert_called_once_with(msg="Unable to create network")

    def test_process_request_present_skips_wait_when_wait_false(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            mock_request = mock.MagicMock()
            mock_request.WaitUntilComplete = mock.MagicMock(return_value=0)
            self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_request)
            self.module.params = {
                'location': 'mock_loc',
                'wait': False
            }

            self.network.process_request()

            self.assertEqual(0, mock_request.WaitUntilComplete.call_count)

    def test_process_request_present_calls_update_when_network_exists_and_is_not_current(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets):
            name = 'ShinyNewName'
            desc = 'ShinyNewDescription'
            self.network.clc.v2.Network.Create = mock.MagicMock()
            self.existing_net.Update = mock.MagicMock()
            self.module.params = {
                'id': 'existing',
                'name': name,
                'description': desc,
                'location': 'mock_loc',
            }

            self.network.process_request()

            self.assertEqual(0, self.network.clc.v2.Network.Create.call_count)
            self.existing_net.Update.assert_called_once_with(name,description=desc,location='mock_loc' )

    def test_process_request_present_calls_update_with_description_when_name_not_provided(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets):
            desc = 'ShinyNewDescription'
            self.network.clc.v2.Network.Create = mock.MagicMock()
            self.existing_net.Update = mock.MagicMock()
            self.module.params = {
                'id': 'existing',
                'description': desc,
                'location': 'mock_loc',
            }

            self.network.process_request()

            self.assertEqual(0, self.network.clc.v2.Network.Create.call_count)
            self.existing_net.Update.assert_called_once_with('existing',description=desc,location='mock_loc' )


    def test_process_request_present_calls_update_when_network_exists_and_only_name_is_not_current(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets):
            name = 'ShinyNewName'
            desc = 'ShinyNewDescription'
            self.network.clc.v2.Network.Create = mock.MagicMock()
            self.existing_net.Update = mock.MagicMock()
            self.module.params = {
                'id': 'existing',
                'name': name,
                'location': 'mock_loc',
            }

            self.network.process_request()

            self.assertEqual(0, self.network.clc.v2.Network.Create.call_count)
            self.existing_net.Update.assert_called_once_with(name, location='mock_loc')



    def test_process_request_present_creates_and_exits_with_expected_network(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets):
            mock_new = mock.MagicMock()
            mock_new.id = '12345'
            mock_new.alias = 'my_alias'
            mock_new.data = {
                'id': 'working',
                'field': 'value'
            }
            self.network.clc.v2.Network = mock.MagicMock(return_value=mock_new)

            mock_request = mock.MagicMock()
            mock_request.WaitUntilComplete = mock.MagicMock(return_value=0)
            self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_request)
            self.module.params = {
                'id': 'working',
                'location': 'mock_loc'
            }

            self.network.process_request()

            self.module.exit_json.assert_called_once_with(changed=True,network=mock_new.data)

    def update_data(self, payload):
        self.existing_net.data = payload

    def test_process_request_present_updates_and_exits_with_expected_network(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets):
            new_name = 'new_name'
            mock_update = self.existing_net
            mock_update.alias = 'my_alias'
            mock_update.data = {
                'id': 'existing',
                'field': 'value'
            }

            expected = mock_update.data
            expected['name'] = new_name

            self.existing_net.Update = mock.MagicMock(side_effect=self.update_data(expected))
            self.module.params = {
                'id': 'existing',
                'name': new_name,
                'location': 'mock_loc'
            }

            self.network.process_request()

            self.module.exit_json.assert_called_once_with(changed=True,network=expected)

    def test_process_request_present_exits_with_expected_request_when_wait_false(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets):
            op_id = "operationId"
            op_uri = "/v2-experimental/operations/xxx/status/operationId"
            mock_request = mock.MagicMock()
            mock_request.id = op_id
            mock_request.uri = op_uri
            mock_requests = create_autospec(clc_sdk.v2.Requests)
            mock_requests.requests = [mock_request]
            self.network.clc.v2.Network.Create = mock.MagicMock(return_value=mock_requests)
            self.module.params = {
                'location': 'mock_loc',
                'wait': False
            }

            self.network.process_request()

            expected = {
                "id": op_id,
                "uri": op_uri
            }

            self.module.exit_json.assert_called_once_with(changed=True,network=expected)


    def test_process_request_for_delete_calls_sdk_delete_and_reports_change(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            self.existing_net.Delete = mock.MagicMock()
            self.module.params = {
                'state': 'absent',
                'id': 'existing',
                'location': 'mock_loc'
            }

            self.network.process_request()

            self.existing_net.Delete.assert_called_once_with(location="mock_loc")
            self.module.exit_json.assert_called_once_with(changed=True, network=None)

    def test_process_request_for_delete_returns_no_change_when_network_not_found(self):
        with patch.object(ClcNetwork, '_populate_networks', return_value=self.mock_nets) as mock_nets:
            self.existing_net.Delete = mock.MagicMock()
            self.module.params = {
                'state': 'absent',
                'id': 'non-existing',
                'location': 'mock_loc'
            }

            self.network.process_request()

            self.assertEqual(0, self.existing_net.Delete.call_count)
            self.module.exit_json.assert_called_once_with(changed=False, network=None)




if __name__ == '__main__':
    unittest.main()
