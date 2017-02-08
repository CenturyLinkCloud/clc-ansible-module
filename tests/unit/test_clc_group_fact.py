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

import clc_ansible_module.clc_group_fact as clc_group_fact
from clc_ansible_module.clc_group_fact import ClcGroupFact

from clc import CLCException
import clc as clc_sdk
import mock
from mock import patch
import unittest

class TestClcGroupFactFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

    def test_process_request(self):
        pass

    def test_define_argument_spec(self):
        result = ClcGroupFact._define_module_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertTrue('argument_spec' in result)
        self.assertEqual(
            result['argument_spec'],
            {'group_id': {'required': True}})

    def test_get_endpoint(self):
        under_test = ClcGroupFact(self.module)
        under_test.api_url = 'http://unittest.example.com'
        under_test.clc_alias = 'test_alias'
        self.assertEqual(
            under_test._get_endpoint('test_group'),
            'http://unittest.example.com/v2/groups/test_alias/test_group')

    def test_set_clc_credentials_from_env(self):
        # Required combination of credentials not passed
        with patch.dict(
                'os.environ', {
                    'CLC_V2_API_URL': 'http://unittest.example.com',
                },
                clear=True):
            under_test = ClcGroupFact(self.module)
            under_test._set_clc_credentials_from_env()
        self.module.fail_json.assert_called_with(
            msg='You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD '
                'environment variables')
        # Token and alias
        with patch.dict(
                'os.environ', {
                    'CLC_V2_API_URL': 'http://unittest.example.com',
                    'CLC_V2_API_TOKEN': 'dummy_token',
                    'CLC_ACCT_ALIAS': 'dummy_alias',
                },
                clear=True):
            under_test = ClcGroupFact(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.v2_api_token, 'dummy_token')
        self.assertEqual(under_test.clc_alias, 'dummy_alias')
        # Username and password
        # Mock requests response from endpoint


if __name__ == '__main__':
    unittest.main()
