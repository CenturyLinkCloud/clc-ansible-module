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

import clc_ansible_utils.clc as clc
from clc_ansible_utils.clc import ApiV2

import mock
from mock import patch
import unittest


class TestClcApiFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

    def test_clc_set_credentials_w_creds(self):
        under_test = ApiV2(self.module)
        with patch.object(under_test, 'call') as mock_method:
            with patch.dict('os.environ',
                            {'CLC_V2_API_USERNAME': 'dummy_username',
                            'CLC_V2_API_PASSWD': 'dummy_passwd'},
                            clear=True):
                under_test._set_clc_credentials_from_env()
        # Should fail with an HTTP error code of 400 for bad user/passwd
        # TODO: Set up better mock to fully test response from API
        mock_method.assert_called_with(
            'POST', '/v2/authentication/login',
            data={'username': 'dummy_username', 'password': 'dummy_passwd'})

    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ApiV2(self.module)
            under_test._set_clc_credentials_from_env()

        self.assertEqual(self.module.fail_json.called, True)

    def test_override_v2_api_url_from_environment(self):
        under_test = ApiV2(self.module)
        original_url = under_test._default_api_url

        under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test._default_api_url, original_url)

        with patch.dict('os.environ',
                        {'CLC_V2_API_URL': 'http://unittest.example.com/'},
                        clear=True):
            under_test._set_clc_credentials_from_env()

        self.assertEqual(under_test.api_url,
                         'http://unittest.example.com/')

    def test_set_user_agent(self):
        under_test = ApiV2(self.module)
        self.assertTrue(hasattr(under_test, '_headers'))
        under_test._set_user_agent()
        self.assertIn('ClcAnsibleModule', under_test._headers['Api-Client'])
        self.assertIn('ClcAnsibleModule', under_test._headers['User-Agent'])
