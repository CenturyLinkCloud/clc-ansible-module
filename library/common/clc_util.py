
def clc_common_argument_spec():
    return dict(
        v1_api_key=dict(),
        v1_api_passwd=dict(no_log=True),
        v2_api_username = dict(),
        v2_api_passwd = dict(no_log=True)
    )
