

### Insure that all modules honor CHECK mode:
See http://docs.ansible.com/developing_modules.html#check-mode and https://docs.ansible.com/playbooks_checkmode.html

1.  Pass ```supports_check_mode=True``` when instantiating the AnsibleModule object.
2.  Place ```if not module.check_mode:``` before any call to the CLC API that would change state.
3.  Insure that module.exit_json only returns items actually changed from ```changed=```

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

Insure that all classes and functions should have docstrings that follow the conventions in [PEP257](https://www.python.org/dev/peps/pep-0257/).
