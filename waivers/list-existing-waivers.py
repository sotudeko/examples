
import json
import requests
import os
import os.path
import sys
import shutil
import csv


iqurl = sys.argv[1]
iquser = sys.argv[2]
iqpwd = sys.argv[3]

datadir = "datafiles"

if os.path.exists(datadir):
	shutil.rmtree(datadir)

os.mkdir(datadir)

existingWaiversCsv = "{}/{}".format(datadir, "existingWaivers.csv")
existingWaiversJson = "{}/{}".format(datadir, "existingWaivers.json")

def getNexusIqData(api):
	url = "{}{}" . format(iqurl, api)

	req = requests.get(url, auth=(iquser, iqpwd), verify=False)

	if req.status_code == 200:
		res = req.json()
	else:
		res = "Error fetching data"

	return res



def getCVE():
	return "no-cve"


def listWaivers(waivers):

	applicationWaivers = waivers['applicationWaivers']

	with open(existingWaiversCsv, 'w') as fd:
			writer = csv.writer(fd, delimiter='\t')
			for waiver in applicationWaivers:
				applicationPublicId = waiver["application"]["publicId"]

				stages = waiver["stages"]

				for stage in stages:
					stageId = stage["stageId"]
					componentPolicyViolations = stage["componentPolicyViolations"]

					for componentViolation in componentPolicyViolations:
						componentName = componentViolation["component"]["packageUrl"]
						componentHash = componentViolation["component"]["hash"]
						waivedPolicyViolations = componentViolation["waivedPolicyViolations"]

						for waivedPolicyViolation in waivedPolicyViolations:
							policyName = waivedPolicyViolation["policyName"]

							if "vulnerabilityId" in waivedPolicyViolation["policyWaiver"]:
								vulnerabilityId = waivedPolicyViolation["policyWaiver"]["vulnerabilityId"]
							else:
								vulnerabilityId = getCVE()

							comment = waivedPolicyViolation["policyWaiver"]["comment"]

							if "scopeOwnerName" in waivedPolicyViolation["policyWaiver"]:
								scopeOwnerName = waivedPolicyViolation["policyWaiver"]["scopeOwnerName"]
							else:
								scopeOwnerName = "no-scope-name"

							if "scopeOwnerType" in waivedPolicyViolation["policyWaiver"]:
								scopeOwnerType = waivedPolicyViolation["policyWaiver"]["scopeOwnerType"]
							else:
								scopeOwnerType = "no-scope-type"

							if "scopeOwnerId" in waivedPolicyViolation["policyWaiver"]:
								scopeOwnerId = waivedPolicyViolation["policyWaiver"]["scopeOwnerId"]
							else:
								scopeOwnerId = "no-scope-id"

							line = []
							line.append(applicationPublicId)
							line.append(componentName)
							line.append(componentHash)
							line.append(policyName)
							line.append(vulnerabilityId)
							line.append(stageId)
							line.append(comment)
							line.append(scopeOwnerName)
							line.append(scopeOwnerType)
							line.append(scopeOwnerId)

							print(line)
							writer.writerow(line)

	return


def main():
	waivers = getNexusIqData('/api/v2/reports/components/waivers')

	with open(existingWaiversJson, "w") as wfile:
		json.dump(waivers, wfile, indent=2)

	listWaivers(waivers)

				
if __name__ == '__main__':
	main()
