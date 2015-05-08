test:
	nosetests --exe -v --cover-package=clc_loadbalancer,clc_aa_policy,clc_group,clc_package,clc_publicip,clc_server,clc_server_snapshot --cover-erase --cover-branches --cover-inclusive --with-xunit --with-xcoverage
