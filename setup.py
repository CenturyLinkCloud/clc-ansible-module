# Copyright 2016 CenturyLink
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

try:
    from setuptools import setup, find_packages
except ImportError:
    print("clc_ansible_module now needs setuptools in order to build. "
          "Install it using your package manager (usually python-setuptools) "
          "or via pip (pip install setuptools).")
    sys.exit(1)

setup(
    name='clc-ansible-module',
    version='1.1.22',
    description='Centurylink Cloud Ansible Modules',
    author='CenturyLink Cloud',
    author_email='WFAAS-LLFT@centurylink.com',
    url='https://github.com/CenturylinkCloud/clc-ansible-module',
    download_url='https://github.com/CenturylinkCloud/clc-ansible-module.git',
    install_requires=[
        'ansible',
        'clc-sdk==2.44',
        'future',
        'mock',
        'nose',
        'requests>=2.7',
        'setuptools',
    ],
    packages=find_packages(exclude=('tests',)),
    scripts=['clc_inv.py'],
    test_suite='nose.collector',
    tests_require=['nose'],
    keywords='centurylink cloud clc ansible modules'
)
