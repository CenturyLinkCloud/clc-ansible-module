#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib
import urllib2

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcMeta:

    def __init__(self, module):

        self.clc_auth = {}
        self.module = module
        self.meta_api_url = os.environ.get('META_API_URL',
                                           'https://api.runner.ctl.io')

    def create_meta(self, params):

        model = {
            'accountAlias':  self.clc_auth['clc_alias'],
            'jobId' : params.get('jobId'),
            'executionId' : params.get('executionId'),
            'referenceId' : params.get('referenceId'),
            'name' : params.get('name'),
            'description' : params.get('description'),
            'data' : params.get('data')
        }

        state = params.get('state')
        changed = False
        try:
            response = open_url(
                url='{meta_api}/meta/{alias}/references/{id}'.format(
                    meta_api=self.meta_api_url,
                    alias=self.clc_auth['clc_alias'],
                    id=params.get('referenceId')
                ),
                method='POST',
                headers={'Authorization': 'Bearer {token}'.format(
                            token=self.clc_auth['v2_api_token']),
                         'Content-Type': 'application/json'},
                data=json.dumps(model)
            )
            changed = True
            state = 'created'
        except urllib2.HTTPError as ex:
            if ex.code == 409:
                try:
                    response = open_url(
                        url='{meta_api}/meta/{alias}/references/{id}'
                            '/values/{name}'.format(
                                meta_api=self.meta_api_url,
                                alias=self.clc_auth['clc_alias'],
                                id=params.get('referenceId'),
                                name=params.get('name')
                            ),
                        method='PUT',
                        headers={'Authorization': 'Bearer {token}'.format(
                                    token=self.clc_auth['v2_api_token']),
                                 'Content-Type': 'application/json'},
                        data=json.dumps(model)
                    )
                    changed = True
                    state = 'updated'
                except urllib2.HTTPError as ex:
                    return self.module.fail_json(
                        msg='Failed to update metadata with name: {name}. '
                            '{code}: {msg}'.format(name=params.get('name'),
                                                   code=ex.code,
                                                   msg=ex.reason))
            else:
                return self.module.fail_json(
                    msg='Failed to create metadata with name: {name}. '
                        '{code}: {msg}'.format(name=params.get('name'),
                                               code=ex.code,
                                               msg=ex.reason))

        if changed:
            model = json.loads(response.read())
        return self.module.exit_json(
            changed=changed,
            content={'state': state, 'payload': model})

    def delete_meta(self, params):
        state = params.get('state')
        changed = False
        try:
            response = open_url(
                url='{meta_api}/meta/{alias}/references/{id}'
                    '/values/{name}'.format(
                        meta_api=self.meta_api_url,
                        alias=self.clc_auth['clc_alias'],
                        id=params.get('referenceId'),
                        name=params.get('name')
                    ),
                method='DELETE',
                headers={'Authorization': 'Bearer {token}'.format(
                            token=self.clc_auth['v2_api_token'])}
            )
            changed = True
            state = 'deleted'
        except urllib2.HTTPError as ex:
            if ex.code != 404:
                return self.module.fail_json(
                    msg='Failed to delete metadata with name: {name}. '
                        '{msg}'.format(name=params.get('name'),
                                       msg=ex.reason))

        return self.module.exit_json(changed=changed, content={'state': state})

    def process_request(self):
        self.clc_auth = clc_common.authenticate(self.module)

        params = self.module.params
        state = params.get('state')
        if state == 'present':
            return self.create_meta(params)
        elif state == 'absent':
            return self.delete_meta(params)

    @staticmethod
    def _define_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            jobId=dict(type='str', required=True),
            executionId=dict(type='str', required=True),
            referenceId=dict(type='str', required=True),
            name=dict(type='str', required=True),
            description=dict(type='str', required=True),
            data=dict(type='dict', required=True),
            state=dict(type='str', choices=['present', 'absent']))

        return argument_spec


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    module = AnsibleModule(argument_spec=ClcMeta._define_argument_spec(),
                           supports_check_mode=True)
    clc_meta = ClcMeta(module)

    clc_meta.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
from ansible.module_utils.urls import *  # pylint: disable=W0614

if __name__ == '__main__':
    main()
