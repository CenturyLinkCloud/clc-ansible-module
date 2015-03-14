try:
    import clc
except ImportError:
    print "failed=True msg='clc-python-sdk required for this module'"
    sys.exit(1)


def clc_common_argument_spec():
    return dict(
        v1_api_key=dict(),
        v1_api_passwd=dict(no_log=True),
        v2_api_username = dict(),
        v2_api_passwd = dict(no_log=True)
    )

def clc_set_credentials(module):
        v1_api_key = module.params.get('v1_api_key')
        v1_api_passwd = module.params.get('v1_api_passwd')
        v2_api_username = module.params.get('v2_api_username')
        v2_api_passwd = module.params.get('v2_api_passwd')

        clc.v1.SetCredentials(v1_api_key,v1_api_passwd)
        clc.v2.SetCredentials(v2_api_username,v2_api_passwd)

        return clc
