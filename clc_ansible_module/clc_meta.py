#!/usr/bin/python

import requests

class ClcMetaFact:

    def __init__(self, module):
        self.module = module
        self.api_url = ''
        self.headers = {}

        self._set_clc_credentials_from_env()

    def _set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        self.api_url = env.get('RUNNER_META_API_URL', '')
        self.headers = {
            "Authorization": "Bearer " + v2_api_token
        }


    def create_meta(self, accountAlias, refId, attributes):
        # requests.post(self.api_url, payload, header)
        changed = False
        url = self.api_url + "/" + accountAlias
        json = {'referenceId': refId,
                'attributes': attributes}
        result = requests.post(url, json=json, headers=self.headers)
        if result.status_code == 200:
            changed = True
        return changed, result.json()

    def find_meta(self, accountAlias, refId):
        url = self.api_url + "/" + accountAlias + "?referenceId=" + refId
        return False, requests.get(url, headers=self.headers).json()

    def delete_meta(self, accountAlias, id):
        changed = False
        url = self.api_url + "/" + accountAlias + "/" + id
        result = requests.delete(url, headers=self.headers)
        if result.status_code == 204:
            changed = True
            return changed, {}
        else:
            self.module.fail_json("Unable to delete the meta data " + result.content)


    def process_request(self):
        params = self.module.params
        action = params.get('action')
        if action == 'create':
            return self.create_meta(params.get('accountAlias'), params.get('referenceId'), params.get('attributes'))
        elif action == 'fetch':
            return self.find_meta(params.get('accountAlias'), params.get('referenceId'))
        elif action == 'delete':
            return self.delete_meta(params.get('accountAlias'), params.get('id'))


    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            accountAlias=dict(type='str'),
            referenceId=dict(type='str'),
            attributes=dict(type='dict'),
            id=dict(type='str'),
            action=dict(type='str'))


        return {"argument_spec": argument_spec}


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcMetaFact._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_meta_fact = ClcMetaFact(module)

    changed, response = clc_meta_fact.process_request()
    module.exit_json(changed=changed, meta=response)

from ansible.module_utils.basic import *  # pylint: disable=W0614

if __name__ == '__main__':
    main()
