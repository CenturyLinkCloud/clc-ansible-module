#!/usr/bin/python

import clc_group as clc_group
from clc_group import ClcGroup
import clc as clc_sdk
import mock
from mock import patch
import unittest

class TestClcServerFunctions(unittest.TestCase):

    def setUp(self):
        self.clc = mock.MagicMock()
        self.module = mock.MagicMock()
        self.datacenter=mock.MagicMock()


    def test_clc_module_not_found(self):
        # Setup Mock Import Function
        import __builtin__ as builtins
        real_import = builtins.__import__
        def mock_import(name, *args):
            if name == 'clc': raise ImportError
            return real_import(name, *args)
        # Under Test
        with mock.patch('__builtin__.__import__', side_effect=mock_import):
            reload(clc_group)
            clc_group.ClcGroup(self.module)
        # Assert Expected Behavior
        self.module.fail_json.assert_called_with(msg='clc-python-sdk required for this module')


    def test_clc_set_credentials_w_creds(self):
        with patch.dict('os.environ', {'CLC_V2_API_USERNAME': 'hansolo', 'CLC_V2_API_PASSWD': 'falcon'}):
            with patch.object(clc_group, 'clc_sdk') as mock_clc_sdk:
                under_test = ClcGroup(self.module)
                under_test.set_clc_credentials_from_env()

        mock_clc_sdk.v2.SetCredentials.assert_called_once_with(api_username='hansolo', api_passwd='falcon')


    def test_clc_set_credentials_w_no_creds(self):
        with patch.dict('os.environ', {}, clear=True):
            under_test = ClcGroup(self.module)
            under_test.set_clc_credentials_from_env()

        self.assertEqual(self.module.fail_json.called, True)


    def test_get_group(self):
        # Setup
        mock_group = mock.MagicMock(spec=clc_sdk.v2.Group)
        mock_group.name = "MyCoolGroup"

        with patch.object(clc_group, 'clc_sdk') as mock_clc_sdk:
            mock_clc_sdk.v2.Datacenter().Groups().Get.return_value = mock_group
            under_test = ClcGroup(self.module)

            # Function Under Test
            result = under_test._get_group(group_name="MyCoolGroup")

        # Assert Result
        mock_clc_sdk.v2.Datacenter().Groups().Get.assert_called_once_with("MyCoolGroup")
        self.assertEqual(result.name, "MyCoolGroup")
        self.assertEqual(self.module.fail_json.called, False)


    def test_get_group_not_found(self):

        # Setup
        with patch.object(clc_group, 'clc_sdk') as mock_clc_sdk:
            mock_clc_sdk.v2.Datacenter().Groups().Get.side_effect = clc_sdk.CLCException("Group not found")
            under_test = ClcGroup(self.module)

            # Function Under Test
            result = under_test._get_group("MyCoolGroup")

        # Assert Result
        mock_clc_sdk.v2.Datacenter().Groups().Get.assert_called_once_with("MyCoolGroup")
        self.assertEqual(result, None)
        self.assertEqual(self.module.fail_json.called, False)


    def test_get_group_exception(self):
        # Setup
        with patch.object(clc_group, 'clc_sdk') as mock_clc_sdk:
            mock_clc_sdk.v2.Datacenter().Groups().Get.side_effect = clc_sdk.CLCException("other error")
            under_test = ClcGroup(self.module)

            # Function Under Test
            result = under_test._get_group("MyCoolGroup")

        # Assert Result
        mock_clc_sdk.v2.Datacenter().Groups().Get.assert_called_once_with("MyCoolGroup")
        self.assertEqual(result, None)
        self.assertEqual(self.module.fail_json.called, True)



if __name__ == '__main__':
    unittest.main()
