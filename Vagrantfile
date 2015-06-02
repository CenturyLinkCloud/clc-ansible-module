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
