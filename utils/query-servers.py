#!/usr/bin/python

import clc
import os

e = os.environ
v2_api_username = e['CLC_V2_API_USERNAME']
v2_api_passwd = e['CLC_V2_API_PASSWD']

clc.v2.SetCredentials(v2_api_username, v2_api_passwd)

print "Querying Group: Default Group"
servers = clc.v2.Datacenter().Groups().Get("Strongloop-Training").Servers().Servers()
print "Found: " +str(len(servers)) + " servers"

for server in servers:
    print str(server.PublicIPs().public_ips[0])
