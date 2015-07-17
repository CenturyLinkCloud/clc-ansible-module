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

Vagrant.configure(2) do |config|
  config.vm.box = "chef/centos-6.6"
   config.vm.synced_folder "src/main/python/", "/usr/local/lib/"
   config.vm.provision "shell", inline: <<-SHELL
     sudo yum install -y epel-release
     sudo yum install -y python-pip
     sudo yum install -y gcc
     sudo yum install -y pycrypto
     sudo pip install ansible
     sudo pip install clc-sdk
     mkdir /etc/ansible && sudo ln -s /usr/local/lib/clc_inv.py /etc/ansible/hosts
     echo "export ANSIBLE_LIBRARY=/usr/local/lib/clc_ansible_module" >> /home/vagrant/.bashrc
   SHELL
end
