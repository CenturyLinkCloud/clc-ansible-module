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

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException

import mock
from mock import patch
import unittest


class TestClcCommonFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

    def test_authenticate_w_creds(self):
        with patch.object(clc_common, 'call_clc_api') as mock_method:
            with patch.dict('os.environ',
                            {'CLC_V2_API_USERNAME': 'dummy_username',
                            'CLC_V2_API_PASSWD': 'dummy_passwd'},
                            clear=True):
                clc_common.authenticate(self.module)
        # Should fail with an HTTP error code of 400 for bad user/passwd
        test_clc_auth = {
            'v2_api_url': 'https://api.ctl.io/v2/',
        }
        # TODO: Set up better mock to fully test response from API
        mock_method.assert_called_with(
            self.module, test_clc_auth,
            'POST', '/authentication/login',
            data={'username': 'dummy_username', 'password': 'dummy_passwd'})

    def test_authenticate_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            clc_common.authenticate(self.module)
        self.assertEqual(self.module.fail_json.called, True)

    def test_override_v2_api_url_from_environment(self):
        original_url = 'https://api.ctl.io/v2/'
        clc_auth = clc_common.authenticate(self.module)
        self.assertEqual(clc_auth['v2_api_url'], original_url)
        with patch.dict('os.environ',
                        {'CLC_V2_API_URL': 'http://unittest.example.com/',
                         'CLC_V2_API_TOKEN': 'dummy_token',
                         'CLC_ACCT_ALIAS': 'dummy_alias',
                         'CLC_LOCATION': 'dummy_location'},
                        clear=True):
            clc_auth = clc_common.authenticate(self.module)
        self.assertEqual(clc_auth['v2_api_url'], 'http://unittest.example.com/')

    def test_set_user_agent(self):
        headers = clc_common._default_headers()
        self.assertIn('ClcAnsibleModule', headers['Api-Client'])
        self.assertIn('ClcAnsibleModule', headers['User-Agent'])
