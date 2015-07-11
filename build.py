from pybuilder.core import init, use_plugin, Author, before

# declare specific plugins we need to use:
use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.coverage")
use_plugin("python.distutils")
use_plugin("filter_resources")
use_plugin("copy_resources")
use_plugin("source_distribution")
use_plugin("python.sonarqube")
use_plugin("exec")

# define project level attributes:
name = 'clc-ansible-module'
version = '1.0.0'
summary = "Centurylink Cloud Ansible Modules"
description = "Ansible extension modules which allow users to interact with Centurylink Cloud to define and manage cloud components."
authors = [Author ("CenturyLink Cloud", "WFAAS-LLFT@centurylink.com")]
url = 'http://www.centurylinkcloud.com'
license = "CTL Corporate License"
keywords = "centurylink cloud clc ansible modules"

# targets are:
# 	clean	compile_sources	init	package	prepare
#	publish	run_integration_tests	run_unit_tests	verify
default_task="publish"

@init
def initialize( project ):
	#  define unit test preferences and behavours:
	project.set_property("run_unit_tests_command", "export PYTHONPATH=$PYTHONPATH:%s;nosetests -w %s --exe -v --with-xunit --xunit-file=target/reports/nosetests_results.xml" % (project.expand_path("$dir_source_main_python"), project.expand_path("$dir_source_unittest_python")))
	project.set_property("run_unit_tests_propagate_stdout", True)
	project.set_property("run_unit_tests_propagate_stderr", True)
	project.set_property('unittest_module_glob','test_*')
	project.set_property('coverage_threshold_warn',0)
	project.set_property('coverage_break_build', False)
	# ----------------
	# identify all the module source locations:
	project.get_property('filter_resources_glob').append('**/clc_ansible_module/*.py')
	# ----------------
	# install clc-sdk during installation
	project.depends_on("clc-sdk", "==2.20")
	# ----------------
	# execute some installation scripts
	project.set_property('dir_source_main_scripts', 'src/main/python')
	# ----------------
        project.set_property('sonar.projectKey', 'com.ctlts:clc-ansible-module')
        project.set_property('sonar.projectName', name)
        project.set_property('sonar.projectVersion', version)
        project.set_property('sonar.sources','src/main/python/clc-ansible-module')
        project.set_property('sonar.tests','src/unittests')
        project.set_property('sonar.python.coverage.reportPath','target/reports/coverage.xml')
        project.set_property('sonar.python.coveragePlugin','cobertura')
	# identify resource files which should be part of the distribution
	# TODO:  would like to include the exampls in the distro but it is currently not working as expected.
	# project.set_property('copy_resources_target', '$dir_target')
	# project.get_property('copy_resources_glob').append('**/example-playbooks/__init__.py')
	# project.include_file('clc-ansible-module-0.0.4','deploy-servers-to-maint-grp-size.yml')
	# ----------------
