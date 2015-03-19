#!/usr/bin/python

import clc
import os

e = os.environ
v2_api_username = e['CLC_V2_API_USERNAME']
v2_api_passwd = e['CLC_V2_API_PASSWD']

clc.v2.SetCredentials(v2_api_username, v2_api_passwd)

print "Querying Group: Default Group"
servers = clc.v2.Datacenter().Groups().Get("Default Group").Servers().Servers()
print "Found: " +str(len(servers)) + " servers"

requests = []
batchSize = 5
i = 1

for server in servers:
    requests.append(server.Delete())
    print "Deleteing: " + server.name +" (" + str(i) +"/" + str(len(servers)) + ")"

    if i%batchSize == 0:
        sum(requests).WaitUntilComplete()
        requests=[]
        
    i += 1

if len(requests) > 0:
    sum(requests).WaitUntilComplete()
