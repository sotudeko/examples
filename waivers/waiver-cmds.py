
import json
import requests
import os
import os.path
import sys
import csv

iqUrl = sys.argv[1]
iqUser = sys.argv[2]
iqPwd = sys.argv[3]

policyViolationIds = {}


def getNexusIqData(api):
    url = "{}{}" . format(iqUrl, api)

    req = requests.get(url, auth=(iqUser, iqPwd), verify=False)

    if req.status_code == 200:
        res = req.json()
    else:
        res = "Error fetching data"

    return res

def getWaiverCmd(line):

    applicationPublicId = line[0]
    packageUrl = line[1]
    policyName = line[2]
    cve = line[3]
    stage = line[4]
    comment = line[5]
    scopeName = line[6]
    scopeType = line[7]

    policyViolationId = policyViolationIds[policyName]

    _comment = "adding waiver for status override"

    if not comment == "":
        _comment = comment

    cmd = "curl -u " + iqUser + ":" + iqPwd + " -X POST -H \"Content-Type: application/json\" -d " + "'{\"comment\": \"" + _comment + "\"}' " + iqUrl + "/api/v2/policyWaivers/application/" + applicationPublicId + "/" + policyViolationId + "\n"
    return cmd

def policyViolationIdsBuild(policyViolationIdsData):
    policies = policyViolationIdsData["policies"]

    for policy in policies:
        policyName = policy["name"]
        policyId = policy["id"]
        policyViolationIds[policyName] = policyId

    return policyViolationIds


def main():
    policyViolationIdsData = getNexusIqData('/api/v2/policies')
    policyViolationIds = policyViolationIdsBuild(policyViolationIdsData)

    # pfmt = json.dumps(policyViolationIdsData, indent=2)
    # print(pfmt)

    with open("waiverlist.csv") as csvfile:
        csvdata = csv.reader(csvfile, delimiter=',')
        for w in csvdata:
            cmd = getWaiverCmd(w)
            print(cmd)







if __name__ == '__main__':
    main()
