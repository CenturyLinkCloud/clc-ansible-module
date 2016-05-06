

### Ensure that all modules honor CHECK mode:
See http://docs.ansible.com/developing_modules.html#check-mode and https://docs.ansible.com/playbooks_checkmode.html

1.  Pass ```supports_check_mode=True``` when instantiating the AnsibleModule object.
2.  Place ```if not module.check_mode:``` before any call to the CLC API that would change state.
3.  Ensure that module.exit_json only returns items actually changed from ```changed=```

### Standardize wait parameter
All modules should take ```wait``` as a parameter.  It should default to ```True```.  If wait is set to false, then the 
module should not wait for queued actions to complete before finishing.

### Standardize state parameter
All modules should take state as a parameter, and should accept ```present``` and ```absent``` as a minimum.
```python
            state=dict(default='present', choices=['present', 'absent'])
```

### Standardize ```_set_clc_credentials_from_env```
All modules should have a standard ```_set_clc_credentials_from_env``` function that follows this form:

```python
    def _set_clc_credentials_from_env(self):
        """
        Set the CLC Credentials on the sdk by reading environment variables
        :return: none
        """
        env = os.environ
        v2_api_token = env.get('CLC_V2_API_TOKEN', False)
        v2_api_username = env.get('CLC_V2_API_USERNAME', False)
        v2_api_passwd = env.get('CLC_V2_API_PASSWD', False)
        clc_alias = env.get('CLC_ACCT_ALIAS', False)
        api_url = env.get('CLC_V2_API_URL', False)

        if api_url:
            self.clc.defaults.ENDPOINT_URL_V2 = api_url

        if v2_api_token and clc_alias:
            self.clc._LOGIN_TOKEN_V2 = v2_api_token
            self.clc._V2_ENABLED = True
            self.clc.ALIAS = clc_alias
        elif v2_api_username and v2_api_passwd:
            self.clc.v2.SetCredentials(
                api_username=v2_api_username,
                api_passwd=v2_api_passwd)
        else:
            return self.module.fail_json(
                msg="You must set the CLC_V2_API_USERNAME and CLC_V2_API_PASSWD "
                    "environment variables")
```

### Fix or Remove all # TODO lines

No module should have any outstanding TODO lines.   Please implement any outstanding TODOs or remove them and create a card in the backlog.

###  All Modules should have DOCUMENTATION and EXAMPLES strings

See the clc_server module for an example.

### All Classes and Functions should have docstrings

Ensure that all classes and functions should have docstrings that follow the conventions in [PEP257](https://www.python.org/dev/peps/pep-0257/).

### Add copywrite comment to the beginning of each module
This should be included in each file at the very beginning, before the DOCUMENTATION string.

```python
# CenturyLink Cloud Ansible Modules.
#
# These Ansible modules enable the CenturyLink Cloud v2 API to be called
# from an within Ansible Playbook.
#
# This file is part of CenturyLink Cloud, and is maintained
# by the Workflow as a Service Team
#
# Copyright 2015 CenturyLink Cloud
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
#
```

### Ensure the ansible.module_utils.basic import is at the bottom of the file:
The import should be right before main, not at the top of the file.

Main should be invoked like this:
```python
from ansible.module_utils.basic import *  # pylint: disable=W0614
if __name__ == '__main__':
    main()
```

### Ensure that main() is defined at the bottom of the file

For readability, main should be defined just before it's called.  It should be the last function def in the file.

### Ensure that main calls a .process_request() method on a class named for the module

Example: 

```python
def main():
    """
    The main function.  Instantiates the module and calls process_request.
    :return: none
    """
    argument_dict = ClcServer._define_module_argument_spec()
    module = AnsibleModule(supports_check_mode=True, **argument_dict)

    clc_server = ClcServer(module)
    clc_server.process_request()
```

This should not be ```do_work``` or anything other than ```process_request```.  I'm looking at you, anti affinity module.  ;)

### Run autopep8 on the module:

Autopep8 will reformat the module to insure that it complies with the pep8 guidelines.  The autopep8 tool will reformat
the module to comply with standards.  This should be the last thing you do

If you don't already have it, install autopep8:
```
> sudo pip install --upgrade autopep8
```
Run it:

```
> autopep8 --in-place --aggressive --aggressive <filename>
```








