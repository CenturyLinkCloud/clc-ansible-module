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
import urllib2
from StringIO import StringIO

import clc_ansible_module.clc_meta_fact as clc_meta_fact
from clc_ansible_module.clc_meta_fact import ClcMetaFact

import clc_ansible_utils.clc as clc_common


class TestClcMetaFact(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()

    @patch.object(clc_meta_fact, 'open_url')
    @patch.object(clc_common, 'authenticate')
    def test_process_request(self, mock_authenticate, mock_open_url):
        mock_authenticate.return_value = {'clc_alias': 'mock_alias',
                                          'v2_api_token': 'mock_token'}
        mock_open_url.return_value = StringIO('{"metadata": []}')

        under_test = ClcMetaFact(self.module)
        under_test.process_request()

        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_meta_fact, 'open_url')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_exception(self, mock_authenticate, mock_open_url):

        mock_authenticate.return_value = {'clc_alias': 'mock_alias',
                                          'v2_api_token': 'mock_token'}
        mock_open_url.side_effect = urllib2.HTTPError('URL', 400, 'Fail', {},
                                                      StringIO('Mock'))
        under_test = ClcMetaFact(self.module)
        under_test.process_request()

        self.module.fail_json.assert_called_once_with(
            msg='Failed to fetch metadata facts. Fail')

    def test_define_argument_spec(self):
        result = ClcMetaFact._define_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertTrue('argument_spec' in result)
        self.assertEqual(
            result['argument_spec'],
            {'jobId': {'type': 'str', 'required': False, 'default': None},
             'executionId': {'type': 'str', 'required': False, 'default': None},
             'referenceId': {'type': 'str', 'required': False, 'default': None},
             'name': {'type': 'str', 'required': False, 'default': None}})

    @patch.object(clc_meta_fact, 'AnsibleModule')
    @patch.object(clc_meta_fact, 'ClcMetaFact')
    def test_main(self, mock_ClcMetaFact, mock_AnsibleModule):
        mock_ClcMetaFact_instance  = mock.MagicMock()
        mock_AnsibleModule_instance = mock.MagicMock()
        mock_ClcMetaFact.return_value = mock_ClcMetaFact_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_meta_fact.main()

        mock_ClcMetaFact.assert_called_once_with(
            mock_AnsibleModule_instance)
        assert mock_ClcMetaFact_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()
