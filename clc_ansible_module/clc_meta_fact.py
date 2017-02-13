#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib2

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcMetaFact:

    def __init__(self, module):
        self.clc_auth = {}
        self.module = module
        self.meta_api_url = os.environ.get('META_API_URL',
                                           'https://api.runner.ctl.io')

    def process_request(self):
        self.clc_auth = clc_common.authenticate(self.module)

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

        response = None
        try:
            response = open_url(
                url='{meta_api}/meta/{alias}'.format(
                    meta_api=self.meta_api_url,
                    alias=self.clc_auth['clc_alias']),
                method='POST',
                data=gq,
                headers={'Authorization': 'Bearer {token}'.format(
                            token=self.clc_auth['v2_api_token']),
                         'Content-Type': 'text/plain'})
        except urllib2.HTTPError as ex:
            self.module.fail_json(
                msg='Failed to fetch metadata facts. {msg}'.format(
                    msg=ex.reason))

        return self.module.exit_json(
            changed=False,
            content={'data': json.loads(response.read())})

    @staticmethod
    def _define_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            jobId=dict(type='str', required=False, default=None),
            executionId=dict(type='str', required=False, default=None),
            referenceId=dict(type='str', required=False, default=None),
            name=dict(type='str', required=False, default=None))

        return argument_spec


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(argument_spec=ClcMetaFact._define_argument_spec(),
                           supports_check_mode=True)
    clc_meta_fact = ClcMetaFact(module)

    clc_meta_fact.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
from ansible.module_utils.urls import *  # pylint: disable=W0614

if __name__ == '__main__':
    main()
