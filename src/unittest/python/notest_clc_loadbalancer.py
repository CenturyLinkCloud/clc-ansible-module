#!/usr/bin/python

import clc_ansible_module.clc_loadbalancer as clc_loadbalancer
from clc_ansible_module.clc_loadbalancer import ClcLoadBalancer
import clc as clc_sdk
import mock
from mock import patch
import unittest

class TestClcLoadbalancerFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter=mock.MagicMock()

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, 'set_clc_credentials_from_env')
    def test_process_request_state_present(self,
                                           mock_set_clc_credentials,
                                           mock_clc_sdk):

        # Setup
        self.module.params = {
            'state': 'present'
        }
        mock_loadbalancer_response = [{'name': 'TEST_LB'}]

        mock_clc_sdk.v2.API.Call.return_value = mock_loadbalancer_response
        # TODO: Mock a response to API.Call('POST')

        # Under Test
        under_test = ClcLoadBalancer(self.module)
        under_test.process_request()

        # Assert
        self.module.exit_json.assert_called_once_with(changed=True, loadbalancer = [{'name': 'TEST_LB'}])
        self.assertFalse(self.module.fail_json.called)

    @patch.object(clc_loadbalancer, 'clc_sdk')
    @patch.object(ClcLoadBalancer, 'set_clc_credentials_from_env')
    def test_process_request_state_absent(self,
                                          mock_set_clc_credentials,
                                          mock_clc_sdk):
        #Setup
        self.module.params = {
            'state': 'absent',
            'name': 'TEST_LB'
        }
        mock_loadbalancer_response = [{'name': 'TEST_LB'}]
        mock_clc_sdk.v2.API.Call.return_value = mock_loadbalancer_response

        test = ClcLoadBalancer(self.module)
        test.process_request()

        #Assertions
        self.module.exit_json.assert_called_once_with(changed=True, loadbalancer=[{'name': 'TEST_LB'}])
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
            reload(clc_loadbalancer)
            clc_loadbalancer.ClcLoadBalancer(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')

        # Reset clc_group
        reload(clc_loadbalancer)

    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(clc_loadbalancer, 'clc_sdk') as mock_clc_sdk:
                under_test = ClcLoadBalancer(self.module)
                under_test.set_clc_credentials_from_env()

        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')


    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcLoadBalancer(self.module)
            under_test.set_clc_credentials_from_env()

        self.assertEqual(self.module.fail_json.called, True)

    def test_define_argument_spec(self):
        result = ClcLoadBalancer.define_argument_spec()
        self.assertIsInstance(result, dict)

    @patch.object(clc_loadbalancer, 'AnsibleModule')
    @patch.object(clc_loadbalancer, 'ClcLoadBalancer')
    def test_main(self, mock_ClcLoadBalancer, mock_AnsibleModule):
        mock_ClcLoadBalancer_instance          = mock.MagicMock()
        mock_AnsibleModule_instance     = mock.MagicMock()
        mock_ClcLoadBalancer.return_value      = mock_ClcLoadBalancer_instance
        mock_AnsibleModule.return_value = mock_AnsibleModule_instance

        clc_loadbalancer.main()

        mock_ClcLoadBalancer.assert_called_once_with(mock_AnsibleModule_instance)
        mock_ClcLoadBalancer_instance.process_request.assert_called_once

if __name__ == '__main__':
    unittest.main()
