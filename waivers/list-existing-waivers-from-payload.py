
import json
import requests
import os
import os.path
import sys
import shutil

waiverPayload = sys.argv[1]

datadir = "datafiles"

if os.path.exists(datadir):
	shutil.rmtree(datadir)

os.mkdir(datadir)

existingWaiversCsv = "{}/{}".format(datadir, "existingWaivers.csv")
existingWaiversJson = "{}/{}".format(datadir, "existingWaivers.json")


def getCVE():
	return "no-cve"


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

						if componentViolation["component"]["packageUrl"] is not None:
							componentName = componentViolation["component"]["packageUrl"]
						else:
							componentName = "no-component-name"

						componentHash = componentViolation["component"]["hash"]
						waivedPolicyViolations = componentViolation["waivedPolicyViolations"]

						for waivedPolicyViolation in waivedPolicyViolations:
							policyName = waivedPolicyViolation["policyName"]

							if "vulnerabilityId" in waivedPolicyViolation["policyWaiver"].keys():
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

							line = applicationPublicId + "," + componentName + "," + componentHash + "," + policyName + "," + vulnerabilityId + "," + stageId + "," + comment + "," + scopeOwnerName + "," + scopeOwnerType + "\n"
							print(line)
							fd.write(line)

	return


def main():
	f = open(waiverPayload)
	waivers = json.load(f)

	with open(existingWaiversJson, "w") as wfile:
		json.dump(waivers, wfile, indent=2)

	listWaivers(waivers)

				
if __name__ == '__main__':
	main()
