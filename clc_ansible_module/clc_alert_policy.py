#!/usr/bin/env python

# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud, and is maintained
# by the Workflow as a Service Team
#
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
#
# CenturyLink Cloud: http://www.CenturyLinkCloud.com
# API Documentation: https://www.centurylinkcloud.com/api-docs/v2/

DOCUMENTATION = '''
module: clc_alert_policy
short_description: Create or Delete Alert Policies at CenturyLink Cloud.
description:
  - An Ansible module to Create or Delete Alert Policies at CenturyLink Cloud.
version_added: "2.0"
options:
  alias:
    description:
      - The alias of your CLC Account
    required: True
  name:
    description:
      - The name of the alert policy. This is mutually exclusive with id
    required: False
    default: None
  id:
    description:
      - The alert policy id. This is mutually exclusive with name
    required: False
    default: None
  alert_recipients:
    description:
      - A list of recipient email ids to notify the alert.
        This is required for state 'present'
    required: False
    default: None
  metric:
    description:
      - The metric on which to measure the condition that will trigger the alert.
        This is required for state 'present'
    required: False
    default: None
    choices: ['cpu','memory','disk']
  duration:
    description:
      - The length of time in minutes that the condition must exceed the threshold.
        This is required for state 'present'
    required: False
    default: None
  threshold:
    description:
      - The threshold that will trigger the alert when the metric equals or exceeds it.
        This is required for state 'present'
        This number represents a percentage and must be a value between 5.0 - 95.0 that is a multiple of 5.0
    required: False
    default: None
  state:
    description:
      - Whether to create or delete the policy.
    required: False
    default: present
    choices: ['present','absent']
requirements:
    - python = 2.7
author: "CLC Runner (@clc-runner)"
notes:
    - To use this module, it is required to set the below environment variables which enables access to the
      Centurylink Cloud
          - CLC_V2_API_USERNAME, the account login id for the centurylink cloud
          - CLC_V2_API_PASSWORD, the account password for the centurylink cloud
    - Alternatively, the module accepts the API token and account alias. The API token can be generated using the
      CLC account login and password via the HTTP api call @ https://api.ctl.io/v2/authentication/login
          - CLC_V2_API_TOKEN, the API token generated from https://api.ctl.io/v2/authentication/login
          - CLC_ACCT_ALIAS, the account alias associated with the centurylink cloud
    - Users can set CLC_V2_API_URL to specify an endpoint for pointing to a different CLC environment.
'''

EXAMPLES = '''
# Note - You must set the CLC_V2_API_USERNAME And CLC_V2_API_PASSWD Environment variables before running these examples

---
- name: Create Alert Policy Example
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Create an Alert Policy for disk above 80% for 5 minutes
      clc_alert_policy:
        alias: wfad
        name: 'alert for disk > 80%'
        alert_recipients:
            - test1@centurylink.com
            - test2@centurylink.com
        metric: 'disk'
        duration: '00:05:00'
        threshold: 80
        state: present
      register: policy

    - name: debug
      debug: var=policy

---
- name: Delete Alert Policy Example
  hosts: localhost
  gather_facts: False
  connection: local
  tasks:
    - name: Delete an Alert Policy
      clc_alert_policy:
        alias: wfad
        name: 'alert for disk > 80%'
        state: absent
      register: policy

    - name: debug
      debug: var=policy
'''

RETURN = '''
changed:
    description: A flag indicating if any change was made or not
    returned: success
    type: boolean
    sample: True
policy:
    description: The alert policy information
    returned: success
    type: dict
    sample:
        {
            "actions": [
                {
                "action": "email",
                "settings": {
                    "recipients": [
                        "user1@domain.com",
                        "user1@domain.com"
                    ]
                }
                }
            ],
            "id": "ba54ac54a60d4a4f1ed6d48c1ce240a7",
            "links": [
                {
                "href": "/v2/alertPolicies/alias/ba54ac54a60d4a4fb1d6d48c1ce240a7",
                "rel": "self",
                "verbs": [
                    "GET",
                    "DELETE",
                    "PUT"
                ]
                }
            ],
            "name": "test_alert",
            "triggers": [
                {
                "duration": "00:05:00",
                "metric": "disk",
                "threshold": 80.0
                }
            ]
        }
'''

__version__ = '${version}'

import clc_ansible_utils.clc as clc_common
from clc_ansible_utils.clc import ClcApiException


class ClcAlertPolicy(object):

    module = None

    def __init__(self, module):
        """
        Construct module
        """
        self.clc_auth = {}
        self.module = module

    @staticmethod
    def _define_module_argument_spec():
        """
        Define the argument spec for the ansible module
        :return: argument spec dictionary
        """
        argument_spec = dict(
            name=dict(default=None),
            id=dict(default=None),
            alias=dict(default=None),
            alert_recipients=dict(type='list', default=None),
            metric=dict(
                choices=[
                    'cpu',
                    'memory',
                    'disk'],
                default=None),
            duration=dict(type='str', default=None),
            threshold=dict(type='int', default=None),
            state=dict(default='present', choices=['present', 'absent'])
        )
        mutually_exclusive = [
            ['name', 'id']
        ]
        return {'argument_spec': argument_spec,
                'mutually_exclusive': mutually_exclusive}

    # Module Behavior Goodness
    def process_request(self):
        """
        Process the request - Main Code Path
        :return: Returns with either an exit_json or fail_json
        """
        p = self.module.params

        self.clc_auth = clc_common.authenticate(self.module)
        if p.get('alias') is None:
            p['alias'] = self.clc_auth['clc_alias']

        if p['state'] == 'present':
            changed, policy = self._ensure_alert_policy_is_present()
        else:
            changed, policy = self._ensure_alert_policy_is_absent()

        self.module.exit_json(changed=changed, policy=policy)

    def _ensure_alert_policy_is_present(self):
        """
        Ensures that the alert policy is present
        :return: (changed, policy)
                 changed: A flag representing if anything is modified
                 policy: the created/updated alert policy
        """
        changed = False
        p = self.module.params
        policy_name = p.get('name')

        if not policy_name:
            self.module.fail_json(msg='Policy name is a required')
        policy = clc_common.find_policy(self.module, self.clc_auth, policy_name,
                                        policy_type='alert')
        if policy is None:
            changed = True
            if not self.module.check_mode:
                policy = self._create_alert_policy()
        else:
            changed, policy = self._ensure_alert_policy_is_updated(policy)
        return changed, policy

    def _ensure_alert_policy_is_absent(self):
        """
        Ensures that the alert policy is absent
        :return: (changed, None)
                 changed: A flag representing if anything is modified
        """
        changed = False
        p = self.module.params
        search_key = (p.get('id') or p.get('name'))
        if not search_key:
            self.module.fail_json(
                msg='Either alert policy id or policy name is required')
        policy = clc_common.find_policy(self.module, self.clc_auth,
                                        search_key, policy_type='alert')
        if policy is not None:
            changed = True
            if not self.module.check_mode:
                self._delete_alert_policy(policy)
        return changed, None

    def _ensure_alert_policy_is_updated(self, alert_policy):
        """
        Ensures the alert policy is updated if anything is changed in the alert policy configuration
        :param alert_policy: the target alert policy
        :return: (changed, policy)
                 changed: A flag representing if anything is modified
                 policy: the updated the alert policy
        """
        changed = False
        p = self.module.params
        alert_policy_id = alert_policy.get('id')
        email_list = p.get('alert_recipients')
        metric = p.get('metric')
        duration = p.get('duration')
        threshold = p.get('threshold')
        policy = alert_policy

        if metric:
            triggers = policy['triggers']
            try:
                i = [str(t['metric']) for t in triggers].index(metric)
                trigger = triggers[i]
                if duration and duration != str(trigger['duration']):
                    changed = True
                elif threshold and float(threshold) != float(
                        trigger['threshold']):
                    changed = True
            except IndexError:
                changed = True
        if not changed and email_list:
            email_current = []
            for action in policy['actions']:
                if action['action'] == 'email':
                    email_current = action['settings']['recipients']
            if set(email_list) != set(email_current):
                changed = True
        if changed and not self.module.check_mode:
            policy = self._update_alert_policy(alert_policy)
        return changed, policy

    def _create_alert_policy(self):
        """
        Create an alert Policy using the CLC API.
        :return: response dictionary from the CLC API.
        """
        p = self.module.params
        alias = p['alias']
        email_list = p['alert_recipients']
        metric = p['metric']
        duration = p['duration']
        threshold = p['threshold']
        policy_name = p['name']
        arguments = {
                'name': policy_name,
                'actions': [{
                    'action': 'email',
                    'settings': {
                        'recipients': email_list
                    }
                }],
                'triggers': [{
                    'metric': metric,
                    'duration': duration,
                    'threshold': threshold
                }]
            }
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'POST', '/alertPolicies/{alias}'.format(alias=alias),
                data=arguments)
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to create alert policy: {name}. {msg}'.format(
                    name=policy_name, msg=e.message))
        return result

    def _update_alert_policy(self, policy):
        """
        Update alert policy using the CLC API.
        :param alert_policy_id: The clc alert policy id
        :return: response dictionary from the CLC API.
        """
        email_action = [p for p in policy['actions']
                        if p['action'] == 'email'][0]
        email_current = email_action['settings']['recipients']

        p = self.module.params
        alias = p['alias']
        policy_name = p['name'] or policy['name']
        email_list = p['alert_recipients'] or email_current
        metric = p['metric']
        if metric:
            triggers = [{
                'metric': metric,
                'duration': p['duration'],
                'threshold': p['threshold']
            }]
        else:
            triggers = policy['triggers']
        arguments = {
                'name': policy_name,
                'actions': [{
                    'action': 'email',
                    'settings': {
                        'recipients': email_list
                    }
                }],
                'triggers': triggers
            }
        try:
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'PUT', '/alertPolicies/{alias}/{id}'.format(
                    alias=alias, id=policy['id']),
                data=arguments)
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to update alert policy: {name}. {msg}'.format(
                    name=policy_name, msg=e.message))
        return result

    def _delete_alert_policy(self, policy):
        """
        Delete an alert policy using the CLC API.
        :param alias : the account alias
        :param policy: the alert policy
        :return: response dictionary from the CLC API.
        """
        alias = self.module.params['alias']
        try:
            # Returns 200 No Content
            result = clc_common.call_clc_api(
                self.module, self.clc_auth,
                'DELETE', '/alertPolicies/{alias}/{id}'.format(
                    alias=alias, id=policy['id']))
        except ClcApiException as e:
            return self.module.fail_json(
                msg='Unable to delete alert policy id: {id}. {msg}'.format(
                    id=policy['id'], msg=e.message))
        return result


def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcAlertPolicy._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)
    clc_alert_policy = ClcAlertPolicy(module)
    clc_alert_policy.process_request()

from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
