
import json
import requests
import os
import os.path
import sys


iqurl = sys.argv[1]
iquser = sys.argv[2]
iqpwd = sys.argv[3]

def getNexusIqData(api):
 url = "{}{}" . format(iqurl, api)

 req = requests.get(url, auth=(iquser, iqpwd), verify=False)

 if req.status_code == 200:
  res = req.json()
 else:
  res = "Error fetching data"

 return res

# def cmd:
#     _comment = "adding waiver for status override"
#
#     if not comment == "":
#         _comment = comment
#
#     # add your iq url, user and password
#     iqUrl = "http://iqurl"
#     iqUser = "iquser"
#     iqPwd = "iqpwd"
#     cmd = "curl -u " + iqUser + ":" + iqPwd + " -X POST -H \"Content-Type: application/json\" -d " + "'{\"comment\": \"" + _comment + "\"}' " + iqUrl + "/api/v2/policyWaivers/application/" + applicationPublicId + "/" + policyViolationId + "\n"
#     return cmd

def policyViolationIdsBuild(policyViolationIdsData):
  policyViolationIds = {}
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


if __name__ == '__main__':
    main()
