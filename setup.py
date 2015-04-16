#!/usr/bin/env python
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'CenturyLink Cloud Ansible Module',
    'author': 'Brian Albrecht',
    'url': 'https://github.com/CenturylinkTechnology/clc-ansible-module.git',
    'download_url': 'https://github.com/CenturylinkTechnology/clc-ansible-module',
    'author_email': 'brian.albrecht@centurylink.com',
    'version': '0.0.1',
    'install_requires': ['clc-sdk'],
    'packages': [],
    'scripts': [],
    'name': 'clc-ansible-module'
}

setup(**config)
