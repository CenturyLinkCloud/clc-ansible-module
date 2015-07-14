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
