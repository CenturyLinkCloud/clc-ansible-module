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
import requests
from uuid import UUID
import clc as clc_sdk
from clc import CLCException
from clc import APIFailedResponse
import json
import mock
from mock import patch, create_autospec

import clc_ansible_module.clc_loadbalancer_fact as clc_loadbalancer_fact
from clc_ansible_module.clc_loadbalancer_fact import ClcLoadbalancerFact

class TestClcLoadbalancerFact(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        real_import = __import__

        def mock_import(name, *args):
            if name == 'clc':
                raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_loadbalancer_fact)
            ClcLoadbalancerFact(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(
            msg='clc-python-sdk required for this module')

        # Reset
        reload(clc_loadbalancer_fact)

    def test_requests_invalid_version(self):
        # Setup Mock Import Function
        real_import = __import__

        def mock_import(name, *args):
            if name == 'requests':
                args[0]['requests'].__version__ = '2.4.0'
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_loadbalancer_fact)
            ClcLoadbalancerFact(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(
            msg='requests library  version should be >= 2.5.0')

        # Reset
        reload(clc_loadbalancer_fact)

    def test_requests_module_not_found(self):
        # Setup Mock Import Function
        real_import = __import__

        def mock_import(name, *args):
            if name == 'requests':
                args[0]['requests'].__version__ = '2.7.0'
                raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_loadbalancer_fact)
            ClcLoadbalancerFact(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(
            msg='requests library is required for this module')

        # Reset
        reload(clc_loadbalancer_fact)

    def test_process_request(self):
        pass

    def test_define_argument_spec(self):
        result = ClcLoadbalancerFact._define_module_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertTrue('argument_spec' in result)
        self.assertEqual(
            result['argument_spec'],
            {'name': {'required': True},
             'location': {'required': True},
             'alias': {'required': True}})

    def test_set_clc_credentials_from_env(self):
        # Required combination of credentials not passed
        with patch.dict('os.environ', {
                'CLC_V2_API_URL': 'http://unittest.example.com', }):
            under_test = ClcLoadbalancerFact(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc.defaults.ENDPOINT_URL_V2,
                         'http://unittest.example.com')
        self.module.fail_json.assert_called_with(
            msg='You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD '
                'environment variables')
        # Token and alias
        with patch.dict('os.environ', {
                'CLC_V2_API_URL': 'http://unittest.example.com',
                'CLC_V2_API_TOKEN': 'dummy_token',
                'CLC_ACCT_ALIAS': 'dummy_alias'}):
            under_test = ClcLoadbalancerFact(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummy_token')
        self.assertTrue(under_test.clc._V2_ENABLED)
        self.assertEqual(under_test.clc.ALIAS, 'dummy_alias')
        # Username and password
        # Mock requests response from endpoint

    def test_get_loadbalancer_list(self):
        pass

    def test_loadbalancer_id(self):
        under_test = ClcLoadbalancerFact(self.module)
        # Figure out correct object type
        under_test.lb_dict = [
            {'name': 'lb1', 'id': 'lb_id1'},
            {'name': 'lb2', 'id': 'lb_id2'},
            {'name': 'lb4', 'id': 'lb_id4'},
        ]
        self.assertEqual(under_test._get_loadbalancer_id('lb1'), 'lb_id1')
        self.assertEqual(under_test._get_loadbalancer_id('lb2'), 'lb_id2')
        self.assertIsNone(under_test._get_loadbalancer_id('lb3'))

    def test_get_endpoint(self):
        pass


if __name__ == '__main__':
    unittest.main()
