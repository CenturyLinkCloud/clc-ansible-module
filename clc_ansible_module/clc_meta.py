#!/usr/bin/python

try:
    import requests
except ImportError:
    REQUESTS_FOUND = False
else:
    REQUESTS_FOUND = True

class ClcMeta:

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


    def create_meta(self, params):

        model = {
            'accountAlias' :  self.clc_alias,
            'jobId' : params.get('jobId'),
            'executionId' : params.get('executionId'),
            'referenceId' : params.get('referenceId'),
            'name' : params.get('name'),
            'description' : params.get('description'),
            'data' : params.get('data')
        }

        state = 'created'
        r = requests.post(self.meta_api_url + '/meta/' + self.clc_alias + '/references/' + params.get('referenceId'),
            json=model, headers={ 'Authorization': 'Bearer ' + self.v2_api_token }, verify=False)

        if r.status_code in [409]:
            state = 'updated'
            r = requests.put(self.meta_api_url + '/meta/' + self.clc_alias + '/references/' + params.get('referenceId') + '/values/' + params.get('name'),
                json=model, headers={ 'Authorization': 'Bearer ' + self.v2_api_token }, verify=False)

        if r.status_code not in [200]:
            self.module.fail_json(msg='Failed to create or update metadata. name:[%s]' % params.get('name'))

        self.module.exit_json(changed=True, content={ 'state' : state, 'payload' : model })

    def delete_meta(self, params):

        state = 'deleted'
        r = requests.delete(self.meta_api_url + '/meta/' + self.clc_alias + '/references/' + params.get('referenceId') + '/values/' + params.get('name'),
            headers={ 'Authorization': 'Bearer ' + self.v2_api_token }, verify=False)

        if r.status_code not in [200, 404]:
            self.module.fail_json(msg='Failed to delete metadata. name:[%s]' % params.get('name'))

        self.module.exit_json(changed=True, content={ 'state' : state })


    def process_request(self):
        params = self.module.params
        state = params.get('state')
        if state == 'present':
            return self.create_meta(params)
        elif state == 'absent':
            return self.delete_meta(params)


    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            jobId=dict(required=True),
            executionId=dict(required=True),
            referenceId=dict(required=True),
            name=dict(required=True),
            description=dict(required=True),
            data=dict(required=True),
            state=dict(choices=['present', 'absent']))


        return {"argument_spec": argument_spec}


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcMeta._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_meta_fact = ClcMeta(module)

    changed, response = clc_meta_fact.process_request()
    module.exit_json(changed=changed, meta=response)

from ansible.module_utils.basic import *  # pylint: disable=W0614

if __name__ == '__main__':
    main()
