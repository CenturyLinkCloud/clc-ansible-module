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

import unittest
import json
import mock
from mock import patch

import clc_ansible_module.clc_loadbalancer_fact as clc_loadbalancer_fact
from clc_ansible_module.clc_loadbalancer_fact import ClcLoadbalancerFact

import clc_ansible_utils.clc as clc_common


class TestClcLoadbalancerFact(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'find_loadbalancer')
    def test_process_request(self, mock_find_loadbalancer, mock_authenticate):
        loadbalancer = {'name': 'mock_name', 'id': 'mock_id'}
        mock_find_loadbalancer.return_value = loadbalancer

        under_test = ClcLoadbalancerFact(self.module)
        under_test.module.params = {
            'name': 'mock_name',
            'alias': 'mock_alias',
            'location': 'mock_dc'
        }

        result = under_test.process_request()

        self.assertEqual(result, loadbalancer)
        self.module.exit_json.assert_called_once_with(changed=False,
                                                      loadbalancer=loadbalancer)
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_common, 'authenticate')
    @patch.object(clc_common, 'find_loadbalancer')
    def test_process_request(self, mock_find_loadbalancer, mock_authenticate):
        mock_find_loadbalancer.return_value = None

        under_test = ClcLoadbalancerFact(self.module)
        under_test.module.params = {
            'name': 'mock_name',
            'alias': 'mock_alias',
            'location': 'mock_dc'
        }

        result = under_test.process_request()

        self.module.fail_json.assert_called_once_with(
            msg='Load balancer with name: mock_name does not exist '
                'for account: mock_alias at location: mock_dc.')

    def test_define_argument_spec(self):
        result = ClcLoadbalancerFact._define_module_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertTrue('argument_spec' in result)
        self.assertEqual(
            result['argument_spec'],
            {'name': {'required': True},
             'location': {'required': True},
             'alias': {'required': True}})

    @patch.object(clc_loadbalancer_fact, 'AnsibleModule')
    @patch.object(clc_loadbalancer_fact, 'ClcLoadbalancerFact')
    def test_main(self, mock_ClcLoadbalancerFact, mock_AnsibleModule):
        mock_ClcLoadbalancerFact_instance  = mock.MagicMock()
        mock_AnsibleModule_instance = mock.MagicMock()
        mock_ClcLoadbalancerFact.return_value = mock_ClcLoadbalancerFact_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_loadbalancer_fact.main()

        mock_ClcLoadbalancerFact.assert_called_once_with(
            mock_AnsibleModule_instance)
        assert mock_ClcLoadbalancerFact_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()
