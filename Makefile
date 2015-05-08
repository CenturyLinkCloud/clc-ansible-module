test:
	nosetests --exe -v --cover-package=clc_aa_policy,clc_group,clc_package,clc_publicip,clc_server,clc_server_snapshot,clc_loadbalancerpool --cover-erase --cover-branches --cover-inclusive --with-xunit --with-xcoverage
