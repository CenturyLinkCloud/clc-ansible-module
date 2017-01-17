#!/usr/bin/python

try:
    import requests
except ImportError:
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True

class ClcMetaFact:

    def __init__(self, module):

        if not REQUESTS_FOUND:
            self.module.fail_json(
                msg='requests library is required for this module')

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
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
        clc_alias = env.get('CLC_ACCT_ALIAS', False)
        self.api_url = env.get('CLC_V2_API_URL', 'https://api.ctl.io')
        self.meta_api_url = env.get('META_API_URL', 'https://api.runner.ctl.io')

        if v2_api_token and clc_alias:

            self.v2_api_token = v2_api_token
            self.clc_alias = clc_alias

        elif v2_api_username and v2_api_passwd:

            r = requests.post(self.api_url + '/v2/authentication/login', json={
                'username': v2_api_username,
                'password': v2_api_passwd
            })

            if r.status_code not in [200]:
                self.module.fail_json(
                    msg='Failed to authenticate with clc V2 api.')

            r = r.json()
            self.v2_api_token = r['bearerToken']
            self.clc_alias = r['accountAlias']

        else:
            return self.module.fail_json(
                msg="You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD "
                    "environment variables")

    def process_request(self):
        params = self.module.params
        criteria = ''
        if params.get('referenceId'):
            criteria += ' referenceId: "' + params.get('referenceId') + '" '
        if params.get('jobId'):
            criteria += ' jobId: "' + params.get('jobId') + '" '
        if params.get('executionId'):
            criteria += ' executionId: "' + params.get('executionId') + '" '
        if params.get('name'):
            criteria += ' name: "' + params.get('name') + '" '

        gq = '{ metadata(' + criteria + ') { id referenceId jobId executionId name description data { ... on Config { type key value } ... on Instance { type value } } } }'

        r = requests.post(self.meta_api_url + '/meta/' + self.clc_alias,
            data=gq, headers={ 'Authorization': 'Bearer ' + self.v2_api_token, 'Content-Type' : 'text/plain' }, verify=False)

        if r.status_code not in [200]:
            # self.module.fail_json(msg='Failed to fetch metadata facts.')
            self.module.exit_json(changed=True, content={ 'data' : r.text })

        self.module.exit_json(changed=True, content={ 'data' : r.json() })


    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            jobId=dict(required=False, default=False),
            executionId=dict(required=False, default=False),
            referenceId=dict(required=False, default=False),
            name=dict(required=False, default=False))

        return {"argument_spec": argument_spec}


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcMetaFact._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    ClcMetaFact(module).process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614

if __name__ == '__main__':
    main()
