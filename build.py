from pybuilder.core import init, use_plugin, Author

# declare specific plugins we need to use:
use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.coverage")
use_plugin("python.distutils")
use_plugin("filter_resources")
use_plugin("copy_resources")
use_plugin("source_distribution")

# define project level attributes:
version = '0.0.4'
summary = "Centurylink Cloud Ansible Modules"
description = "Ansible extension modules which allow users to interact with Centurylink Cloud to define and manage cloud components."
authors = [Author ("CenturyLink Cloud", "WFAAS-LLFT@centurylink.com")]
url = 'http://www.centurylinkcloud.com'
license = "CTL Corporate License"

# targets are:
# 	clean	compile_sources	init	package	prepare
#	publish	run_integration_tests	run_unit_tests	verify
default_task="publish"

@init
def initialize( project ):
	# define unit test preferences and behavours:
	project.set_property('unittest_module_glob','test_*')
	project.set_property('coverage_threshold_warn',0)
	project.set_property('coverage_break_build', False)
	# ----------------
	# identify all the module source locations:
	project.get_property('filter_resources_glob').append('**/inventory/__init__.py')
	project.get_property('filter_resources_glob').append('**/modules/__init__.py')
	project.get_property('filter_resources_glob').append('**/utils/__init__.py')
	# ----------------
	# install clc-sdk during installation
	project.depends_on("clc-sdk")
	# ----------------
	# execute some installation scripts
	project.set_property('dir_source_main_scripts', 'src/main/python')
	# ----------------
	# identify resource files which should be part of the distribution
    # TODO:  would like to include the exampls in the distro but it is currently not working as expected.
	# project.set_property('copy_resources_target', '$dir_target')
	# project.get_property('copy_resources_glob').append('**/example-playbooks/__init__.py')
	# project.include_file('clc-ansible-module-0.0.4','deploy-servers-to-maint-grp-size.yml')
	# ----------------

	
