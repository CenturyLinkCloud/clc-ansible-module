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

FROM ansible/centos7-ansible
MAINTAINER WFaaS

# install git and add the pub key
RUN yum install -y git
RUN yum install -y epel-release
RUN yum install -y python-pip
RUN yum install -y gcc
RUN yum install -y pycrypto

# create an ansible.cfg
RUN echo "[defaults]" > /etc/ansible/ansible.cfg
RUN echo "inventory = /bin/clc_inv.py" >> /etc/ansible/ansible.cfg

## add clc sdk and module
RUN pip install clc-sdk==2.20 clc-ansible-module

## Set ANSIBLE_LIBRARY path
ENV ANSIBLE_LIBRARY /usr/lib/python2.7/site-packages/clc_ansible_module/
