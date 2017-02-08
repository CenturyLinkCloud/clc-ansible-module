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
import mock
from mock import patch

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import clc_ansible_module.clc_network_fact as clc_network_fact
from clc_ansible_module.clc_network_fact import ClcNetworkFact


def FakeAnsibleModule():
    module = mock.MagicMock()
    module.check_mode = False
    module.params = {}
    return module


class TestClcNetworkFactFunctions(unittest.TestCase):

    def setUp(self):
        self.module = FakeAnsibleModule()

        self.mock_net1 = mock.MagicMock()
        self.mock_net1.id = 'mock_id1'
        self.mock_net1.name = 'mock_name1'
        self.mock_net1.data = {'id': 'mock_id1', 'name': 'mock_name1'}
        self.mock_net2 = mock.MagicMock()
        self.mock_net2.id = 'mock_id2'
        self.mock_net2.name = 'mock_name2'
        self.mock_net2.data = {'id': 'mock_id2', 'name': 'mock_name2'}

        self.networks_existing = [self.mock_net1, self.mock_net2]

        self.clc_auth = {'v2_api_url': 'https://api.ctl.io/v2/',
                         'clc_alias': 'mock_alias'}

    @patch.object(clc_common, 'networks_in_datacenter')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_list_networks(self,
                                           mock_authenticate,
                                           mock_networks_datacenter):
        params = {'location': 'mock_dc'}
        mock_authenticate.return_value = self.clc_auth
        mock_networks_datacenter.return_value = self.networks_existing

        under_test = ClcNetworkFact(self.module)
        under_test.module.params = params

        under_test.process_request()

        self.module.exit_json.assert_called_once_with(
            networks=[self.mock_net1.data, self.mock_net2.data])

    @patch.object(clc_common, 'networks_in_datacenter')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_network_found(self,
                                           mock_authenticate,
                                           mock_networks_datacenter):
        params = {'location': 'mock_dc', 'id': 'mock_id1'}
        mock_authenticate.return_value = self.clc_auth
        mock_networks_datacenter.return_value = self.networks_existing

        under_test = ClcNetworkFact(self.module)
        under_test.module.params = params

        under_test.process_request()

        self.module.exit_json.assert_called_once_with(
            network=self.mock_net1.data)

    @patch.object(clc_common, 'networks_in_datacenter')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_network_not_found(self,
                                           mock_authenticate,
                                           mock_networks_datacenter):
        params = {'location': 'mock_dc', 'id': 'fake_id'}
        mock_authenticate.return_value = self.clc_auth
        mock_networks_datacenter.return_value = self.networks_existing

        under_test = ClcNetworkFact(self.module)
        under_test.module.params = params

        under_test.process_request()

        self.module.fail_json.assert_called_once_with(
            msg='Network: {id} does not exist in location: {location}.'.format(
                id=params['id'], location=params['location']))

    def test_define_argument_spec(self):
        result = ClcNetworkFact._define_module_argument_spec()
        self.assertIsInstance(result, dict)
        #self.assertTrue('argument_spec' in result)
        self.assertEqual(
            result,
            {'id': {'required': False},
             'location': {'required': True}})


if __name__ == '__main__':
    unittest.main()
