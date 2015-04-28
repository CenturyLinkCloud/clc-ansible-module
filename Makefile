test:
	nosetests --exe -v --cover-package=\$(ls|grep py|grep -v pyc|sed -e 's/[.]py$//'|paste -s -d ',' -) --cover-erase --cover-branches --cover-inclusive --with-xunit --with-xcoverage
