#!/usr/bin/python

import clc_aa_policy as clc_aa_policy
from clc_aa_policy import ClcAntiAffinityPolicy
import clc as clc_sdk
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
        module = FakeAnsibleModule()
        self.policy = ClcAntiAffinityPolicy(module)
        self.policy.module.exit_json = mock.MagicMock()

    def testNoCreds(self):
        self.policy.module.fail_json = mock.MagicMock(side_effect=Exception('nocreds'))
        try:
            result = self.policy.do_work()
        except:
            pass
        self.assertEqual(self.policy.module.fail_json.called, True)
        #self.policy.module.fail_json.assert_called_once_with(msg="you must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD environment variables")

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
        self.policy.do_work()
        self.policy.module.exit_json.assert_called_once_with(changed=False,policy=None)


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
        self.policy.do_work()
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
        self.policy.do_work()
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
        self.policy.do_work()
        #self.policy.module.exit_json.assert_called_once_with(changed=True,policy=None)


if __name__ == '__main__':
    unittest.main()