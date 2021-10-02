
import json
import requests
import os
import os.path
import sys

iqurl = sys.argv[1]
iquser = sys.argv[2]
iqpwd = sys.argv[3]

datadir = "datafiles"

if os.path.exists(datadir):
	os.rmdir(datadir)

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


def listWaivers(waivers):

	applicationWaivers = waivers['applicationWaivers']

	with open(existingWaiversCsv, 'w') as fd:
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
							vulnerabilityId = waivedPolicyViolation["policyWaiver"]["vulnerabilityId"]
							comment = waivedPolicyViolation["policyWaiver"]["comment"]
							scopeOwnerName = waivedPolicyViolation["policyWaiver"]["scopeOwnerName"]
							scopeOwnerType = waivedPolicyViolation["policyWaiver"]["scopeOwnerType"]

							line = applicationPublicId + "," + componentName + "," + componentHash + "," + policyName + "," + vulnerabilityId + "," + stageId + "," + comment + "," + scopeOwnerName + "," + scopeOwnerType + "\n"
							print(line)
							fd.write(line)

	return


def main():
	waivers = getNexusIqData('/api/v2/reports/components/waivers')

	with open(existingWaiversJson, "w") as wfile:
		json.dump(waivers, wfile, indent=2)

	listWaivers(waivers)

				
if __name__ == '__main__':
	main()
