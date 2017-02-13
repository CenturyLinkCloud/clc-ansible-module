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

import clc_ansible_module.clc_meta as clc_meta
from clc_ansible_module.clc_meta import ClcMeta

import clc_ansible_utils.clc as clc_common


class TestClcMeta(unittest.TestCase):

    def setUp(self):
        self.module = mock.MagicMock()
        self.clc_auth = {'clc_alias': 'mock_alias',
                         'v2_api_token': 'mock_token'}

    @patch.object(ClcMeta, 'create_meta')
    @patch.object(ClcMeta, 'delete_meta')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_state_present(self, mock_authenticate,
                                           mock_delete, mock_create):
        under_test = ClcMeta(self.module)
        under_test.module.params = {'state': 'present'}

        under_test.process_request()

        self.assertTrue(mock_create.called)
        self.assertFalse(mock_delete.called)

    @patch.object(ClcMeta, 'create_meta')
    @patch.object(ClcMeta, 'delete_meta')
    @patch.object(clc_common, 'authenticate')
    def test_process_request_state_absent(self, mock_authenticate,
                                          mock_delete, mock_create):
        under_test = ClcMeta(self.module)
        under_test.module.params = {'state': 'absent'}

        under_test.process_request()

        self.assertFalse(mock_create.called)
        self.assertTrue(mock_delete.called)

    @patch.object(clc_meta, 'open_url')
    @patch.object(clc_common, 'authenticate')
    def test_create_meta_create(self, mock_authenticate, mock_open_url):
        params = {
            'state': 'present',
            'name': 'mock_name',
            'referenceId': 'mock_id'
        }
        mock_authenticate.return_value = {'clc_alias': 'mock_alias',
                                          'v2_api_token': 'mock_token'}
        mock_open_url.return_value = StringIO('{}')
        under_test = ClcMeta(self.module)
        under_test.clc_auth = self.clc_auth
        under_test.create_meta(params)

        self.assertFalse(self.module.fail_json.called)
        self.module.exit_json.assert_called_once_with(
            changed=True, content={'state': 'created', 'payload': {}})

    @patch.object(clc_meta, 'open_url')
    @patch.object(clc_common, 'authenticate')
    def test_create_meta_update(self, mock_authenticate, mock_open_url):

        params = {
            'state': 'present',
            'name': 'mock_name',
            'referenceId': 'mock_id'
        }
        mock_authenticate.return_value = {'clc_alias': 'mock_alias',
                                          'v2_api_token': 'mock_token'}
        mock_open_url.side_effect = [urllib2.HTTPError('URL', 409, 'Fail', {},
                                                       StringIO('Mock')),
                                     StringIO('{}')]
        under_test = ClcMeta(self.module)
        under_test.clc_auth = self.clc_auth
        under_test.create_meta(params)

        self.assertFalse(self.module.fail_json.called)
        self.module.exit_json.assert_called_once_with(
            changed=True, content={'state': 'updated', 'payload': {}})

    @patch.object(clc_meta, 'open_url')
    @patch.object(clc_common, 'authenticate')
    def test_create_meta_exception_400_400(self, mock_authenticate,
                                           mock_open_url):
        params = {
            'state': 'present',
            'name': 'mock_name',
            'referenceId': 'mock_id'
        }
        mock_authenticate.return_value = {'clc_alias': 'mock_alias',
                                          'v2_api_token': 'mock_token'}
        mock_open_url.side_effect = [urllib2.HTTPError('URL', 400, 'Fail', {},
                                                       StringIO('Mock')),
                                     urllib2.HTTPError('URL', 400, 'Fail', {},
                                                       StringIO('Mock'))]
        under_test = ClcMeta(self.module)
        under_test.clc_auth = self.clc_auth
        under_test.create_meta(params)

        self.module.fail_json.assert_called_once_with(
            msg='Failed to create metadata with name: mock_name. Fail')

    @patch.object(clc_meta, 'open_url')
    @patch.object(clc_common, 'authenticate')
    def test_create_meta_exception_409_400(self, mock_authenticate, mock_open_url):

        params = {
            'state': 'present',
            'name': 'mock_name',
            'referenceId': 'mock_id'
        }
        mock_authenticate.return_value = {'clc_alias': 'mock_alias',
                                          'v2_api_token': 'mock_token'}
        mock_open_url.side_effect = [urllib2.HTTPError('URL', 409, 'Fail', {},
                                                       StringIO('Mock')),
                                     urllib2.HTTPError('URL', 400, 'Fail', {},
                                                       StringIO('Mock'))]
        under_test = ClcMeta(self.module)
        under_test.clc_auth = self.clc_auth
        under_test.create_meta(params)

        self.module.fail_json.assert_called_once_with(
            msg='Failed to update metadata with name: mock_name. Fail')


    @patch.object(clc_meta, 'open_url')
    @patch.object(clc_common, 'authenticate')
    def test_delete_meta(self, mock_authenticate, mock_open_url):
        params = {
            'state': 'absent',
            'name': 'mock_name',
            'referenceId': 'mock_id'
        }
        mock_authenticate.return_value = {'clc_alias': 'mock_alias',
                                          'v2_api_token': 'mock_token'}
        mock_open_url.side_effect = StringIO('{}')
        under_test = ClcMeta(self.module)
        under_test.clc_auth = self.clc_auth
        under_test.delete_meta(params)

        self.assertFalse(self.module.fail_json.called)
        self.module.exit_json.assert_called_once_with(
            changed=True, content={'state': 'deleted'})

    @patch.object(clc_meta, 'open_url')
    @patch.object(clc_common, 'authenticate')
    def test_delete_meta_exception_400(self, mock_authenticate, mock_open_url):

        params = {
            'state': 'absent',
            'name': 'mock_name',
            'referenceId': 'mock_id'
        }
        mock_authenticate.return_value = {'clc_alias': 'mock_alias',
                                          'v2_api_token': 'mock_token'}
        mock_open_url.side_effect = urllib2.HTTPError('URL', 400, 'Fail', {},
                                                      StringIO('Mock'))
        under_test = ClcMeta(self.module)
        under_test.clc_auth = self.clc_auth
        under_test.delete_meta(params)

        self.module.fail_json.assert_called_once_with(
            msg='Failed to delete metadata with name: mock_name. Fail')

    @patch.object(clc_meta, 'open_url')
    @patch.object(clc_common, 'authenticate')
    def test_delete_meta_exception_404(self, mock_authenticate, mock_open_url):

        params = {
            'state': 'absent',
            'name': 'mock_name',
            'referenceId': 'mock_id'
        }
        mock_authenticate.return_value = {'clc_alias': 'mock_alias',
                                          'v2_api_token': 'mock_token'}
        mock_open_url.side_effect = urllib2.HTTPError('URL', 404, 'Fail', {},
                                                      StringIO('Mock'))
        under_test = ClcMeta(self.module)
        under_test.clc_auth = self.clc_auth
        under_test.delete_meta(params)

        self.assertFalse(self.module.fail_json.called)
        self.module.exit_json.assert_called_once_with(
            changed=False, content={'state': 'absent'})

    def test_define_argument_spec(self):
        result = ClcMeta._define_argument_spec()
        self.assertIsInstance(result, dict)
        self.assertTrue('argument_spec' in result)
        self.assertEqual(
            result['argument_spec'],
            {'jobId': {'type': 'str', 'required': True},
             'executionId': {'type': 'str', 'required': True},
             'referenceId': {'type': 'str', 'required': True},
             'name': {'type': 'str', 'required': True},
             'description': {'type': 'str', 'required': True},
             'data': {'type': 'dict', 'required': True},
             'state': {'type': 'str', 'required': True,
                       'choices': ['present', 'absent']}})

    @patch.object(clc_meta, 'AnsibleModule')
    @patch.object(clc_meta, 'ClcMeta')
    def test_main(self, mock_ClcMeta, mock_AnsibleModule):
        mock_ClcMeta_instance  = mock.MagicMock()
        mock_AnsibleModule_instance = mock.MagicMock()
        mock_ClcMeta.return_value = mock_ClcMeta_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_meta.main()

        mock_ClcMeta.assert_called_once_with(
            mock_AnsibleModule_instance)
        assert mock_ClcMeta_instance.process_request.call_count == 1


if __name__ == '__main__':
    unittest.main()
