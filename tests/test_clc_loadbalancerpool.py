#!/usr/bin/python

import clc_loadbalancerpool as clc_loadbalancerpool
from clc_loadbalancerpool import ClcLoadBalancerPool
import clc as clc_sdk
import mock
from mock import patch
import unittest

class TestClcLoadbalancerPoolFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter = mock.MagicMock()

    @patch.object(clc_loadbalancerpool, 'clc_sdk')
    @patch.object(ClcLoadBalancerPool, 'set_clc_credentials_from_env')
    def test_process_request_state_present(self, mock_set_clc_credentials, mock_clc_sdk):
        #Setup
        self.module.params = {
            'location': 'UC1',
            'alias': 'WFAD',
            'port': '80',
            'loadbalancer': 'TEST',
            'state': 'present'
        }

        mock_loadbalancer_response = [{'id': 'test', 'name': 'TEST'}]
        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test', 'name': 'TEST'}],
            [],
            [{'id': 'test', 'name': 'TEST'}]
        ]

        #Under Test
        under_test = ClcLoadBalancerPool(self.module)
        under_test.process_request()

        #Assert
        self.module.exit_json.assert_called_once_with(changed=True, loadbalancerpool = [{'id': 'test', 'name': 'TEST'}])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancerpool, 'clc_sdk')
    @patch.object(ClcLoadBalancerPool, 'set_clc_credentials_from_env')
    def test_process_request_state_absent(self, mock_set_clc_credentials, mock_clc_sdk):
        #Setup
        self.module.params = {
            'location': 'UC1',
            'alias': 'WFAD',
            'port': '80',
            'loadbalancer': 'TEST',
            'state': 'absent'
        }

        mock_clc_sdk.v2.API.Call.side_effect = [
            [{'id': 'test', 'name': 'TEST'}],
            [{'port': '80', 'id':'test'}],
            {}
        ]

        #Under Test
        under_test = ClcLoadBalancerPool(self.module)
        under_test.process_request()

        #Assert
        self.module.exit_json.assert_called_once_with(changed=True, loadbalancerpool = {})
        self.assertFalse(self.module.fail_json.called)

    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_loadbalancerpool)
            clc_loadbalancerpool.ClcLoadBalancerPool(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')

        # Reset clc_group
        reload(clc_loadbalancerpool)

    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(clc_loadbalancerpool, 'clc_sdk') as mock_clc_sdk:
                under_test = ClcLoadBalancerPool(self.module)
                under_test.set_clc_credentials_from_env()

        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')


    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcLoadBalancerPool(self.module)
            under_test.set_clc_credentials_from_env()

        self.assertEqual(self.module.fail_json.called, True)

    def test_define_argument_spec(self):
        result = ClcLoadBalancerPool.define_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(clc_loadbalancerpool, 'AnsibleModule')
    @patch.object(clc_loadbalancerpool, 'ClcLoadBalancerPool')
    def test_main(self, mock_ClcLoadBalancerPool, mock_AnsibleModule):
        mock_ClcLoadBalancerPool_instance          = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcLoadBalancerPool.return_value      = mock_ClcLoadBalancerPool_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_loadbalancerpool.main()

        mock_ClcLoadBalancerPool.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcLoadBalancerPool_instance.process_request.assert_called_once

if __name__ == '__main__':
    unittest.main()
