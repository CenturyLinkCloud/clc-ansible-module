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

import clc_ansible_module.clc_aa_policy as clc_aa_policy
from clc_ansible_module.clc_aa_policy import ClcAntiAffinityPolicy
import clc as clc_sdk
from clc import CLCException
import mock
from mock import patch, create_autospec
import os
import unittest

# This is a pretty brute-force attack at unit testing.
# This is my first stab, so anyone reading this who is more Python-inclined
# is both welcome and encouraged to make it better.

        # self.clc.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')
def FakeAnsibleModule():
    module = mock.MagicMock()
    module.check_mode = False
    module.params = {}
    return module

class TestClcAntiAffinityPolicy(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = FakeAnsibleModule()
        self.policy = ClcAntiAffinityPolicy(self.module)
        self.policy.module.exit_json = mock.MagicMock()
        self.policy_dict = {}



    def notestNoCreds(self):
        self.policy.module.fail_json = mock.MagicMock(side_effect=Exception('nocreds'))
        try:
            result = self.policy.do_work()
        except:
            pass
        self.assertEqual(self.policy.module.fail_json.called, True)

    def testLoginMagic(self):
        self.policy.clc.v2.SetCredentials = mock.MagicMock()
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME':'passWORD', 'CLC_V2_API_PASSWD':'UsErnaME'}):
            try:
                self.policy.process_request()
            except:
                # It'll die, and we don't care
                pass

        self.policy.clc.v2.SetCredentials.assert_called_once_with(api_username='passWORD',api_passwd='UsErnaME')

    @patch.object(clc_aa_policy, 'clc_sdk')
    def test_set_user_agent(self, mock_clc_sdk):
        clc_aa_policy.__version__ = "1"
        ClcAntiAffinityPolicy._set_user_agent(mock_clc_sdk)

        self.assertTrue(mock_clc_sdk.SetRequestsSession.called)

    def testArgumentSpecContract(self):
        args = ClcAntiAffinityPolicy._define_module_argument_spec()
        self.assertEqual(args, dict(
            name=dict(required=True),
            location=dict(required=True),
            state=dict(default='present', choices=['present', 'absent']),
            wait=dict(default=True)
        ))

    def testCreateNoChange(self):
        mock_policy = mock.MagicMock(spec=clc_sdk.v2.AntiAffinity)
        mock_policy.name = 'TestMaster3000'
        mock_policy.data = {}
        self.policy.module.params = {
            'location': 'beer',
            'state': 'present',
            'name': 'TestMaster3000'
        }

        self.policy.clc.v2.AntiAffinity.GetAll = mock.MagicMock(return_value=[mock_policy])
        self.policy.process_request()
        self.policy.module.exit_json.assert_called_once_with(changed=False,policy={})


    def testCreateWithChange(self):
        mock_policy = mock.MagicMock(spec=clc_sdk.v2.AntiAffinity)
        mock_policy.name = 'TestMaster3000'
        mock_policy.data = {'a_thing': 'happened'}
        self.policy.module.params = {
            'location': 'beer',
            'state': 'present',
            'name': 'TestMaster3000'
        }

        self.policy.clc.v2.AntiAffinity.GetAll = mock.MagicMock(return_value=[])
        self.policy.clc.v2.AntiAffinity.Create = mock.MagicMock(return_value=mock_policy)
        self.policy.process_request()
        self.policy.module.exit_json.assert_called_once_with(changed=True,policy=mock_policy.data)

    def testDeleteNoChange(self):
        mock_policy = mock.MagicMock(spec=clc_sdk.v2.AntiAffinity)
        mock_policy.name = 'TestMaster3000'
        mock_policy.data = {}
        self.policy.module.params = {
            'location': 'beer',
            'state': 'absent',
            'name': 'TestMaster3000'
        }

        self.policy.clc.v2.AntiAffinity.GetAll = mock.MagicMock(return_value=[])
        self.policy.process_request()
        self.policy.module.exit_json.assert_called_once_with(changed=False,policy=None)

    def testDeleteWithChange(self):
        mock_policy = mock.MagicMock(spec=clc_sdk.v2.AntiAffinity)
        mock_policy.name = 'TestMaster3000'
        mock_policy.data = {'a_thing': 'happened'}
        self.policy.module.params = {
            'location': 'beer',
            'state': 'absent',
            'name': 'TestMaster3000'
        }

        self.policy.clc.v2.AntiAffinity.GetAll = mock.MagicMock(return_value=[mock_policy])
        self.policy.clc.v2.AntiAffinity.Delete = mock.MagicMock(return_value=None)
        self.policy.process_request()
        self.policy.module.exit_json.assert_called_once_with(changed=True,policy=None)

    @patch.object(ClcAntiAffinityPolicy, 'clc')
    def test_set_clc_credentials_from_env(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_TOKEN': 'dummyToken',
                                       'CLC_ACCT_ALIAS': 'TEST'}):
            self.module.fail_json.called = False
            under_test = ClcAntiAffinityPolicy(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(under_test.clc._LOGIN_TOKEN_V2, 'dummyToken')
        self.assertFalse(mock_clc_sdk.v2.SetCredentials.called)
        self.assertEqual(self.module.fail_json.called, False)

    @patch.object(ClcAntiAffinityPolicy, 'clc')
    def test_set_clc_credentials_w_creds(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'dummyuser', 'CLC_V2_API_PASSWD': 'dummypwd'}):
            under_test = ClcAntiAffinityPolicy(self.module)
            under_test._set_clc_credentials_from_env()
            mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='dummyuser', api_passwd='dummypwd')

    @patch.object(ClcAntiAffinityPolicy, 'clc')
    def test_set_clc_credentials_w_api_url(self, mock_clc_sdk):
        with patch.dict('os.environ', {'CLC_V2_API_URL': 'dummyapiurl'}):
            under_test = ClcAntiAffinityPolicy(self.module)
            under_test._set_clc_credentials_from_env()
            self.assertEqual(under_test.clc.defaults.ENDPOINT_URL_V2, 'dummyapiurl')

    def test_set_clc_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcAntiAffinityPolicy(self.module)
            under_test._set_clc_credentials_from_env()
        self.assertEqual(self.module.fail_json.called, True)

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_aa_policy)
            clc_aa_policy.ClcAntiAffinityPolicy(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')
        reload(clc_aa_policy)

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
            reload(clc_aa_policy)
            clc_aa_policy.ClcAntiAffinityPolicy(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library  version should be >= 2.5.0')
        reload(clc_aa_policy)

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
            reload(clc_aa_policy)
            clc_aa_policy.ClcAntiAffinityPolicy(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='requests library is required for this module')
        reload(clc_aa_policy)

    @patch.object(clc_aa_policy, 'AnsibleModule')
    @patch.object(clc_aa_policy, 'ClcAntiAffinityPolicy')
    def test_main(self, mock_ClcAAPolicy, mock_AnsibleModule):
        mock_ClcAAPolicy_instance       = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcAAPolicy.return_value   = mock_ClcAAPolicy_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_aa_policy.main()

        mock_ClcAAPolicy.assert_called_once_with(mock_AnsibleModule_instance)
        assert mock_ClcAAPolicy_instance.process_request.call_count ==1

    @patch.object(clc_aa_policy, 'clc_sdk')
    def test_create_aa_policy_error(self, mock_clc_sdk):
        under_test = ClcAntiAffinityPolicy(self.module)
        policy = {
            'name': 'dummyname',
            'location': 'dummylocation'
        }
        error = CLCException('Failed')
        error.response_text = 'I am failed'
        mock_clc_sdk.v2.AntiAffinity.Create.side_effect = error
        under_test.clc = mock_clc_sdk
        ret = under_test._create_policy(policy)
        self.module.fail_json.assert_called_with(msg='Failed to create anti affinity policy : dummyname. I am failed')

    @patch.object(clc_aa_policy, 'clc_sdk')
    def test_delete_aa_policy_error(self, mock_clc_sdk):
        under_test = ClcAntiAffinityPolicy(self.module)
        error = CLCException('Failed')
        error.response_text = 'I am failed'
        policy_mock = mock.MagicMock()
        policy_mock.Delete.side_effect = error
        under_test.policy_dict['dummyname'] = policy_mock
        under_test.clc = mock_clc_sdk
        policy = {
            'name': 'dummyname',
            'location': 'dummylocation'
        }
        ret = under_test._delete_policy(policy)
        self.module.fail_json.assert_called_with(msg='Failed to delete anti affinity policy : dummyname. I am failed')



if __name__ == '__main__':
    unittest.main()
