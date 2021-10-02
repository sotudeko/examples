
import json
import requests
import os
import os.path
import sys
import shutil
import csv

waiverPayload = sys.argv[1]

datadir = "datafiles"

if os.path.exists(datadir):
	shutil.rmtree(datadir)

os.mkdir(datadir)

existingWaiversCsv = "{}/{}".format(datadir, "existingWaivers.csv")
existingWaiversJson = "{}/{}".format(datadir, "existingWaivers.json")


def cveExists(cve, cveValue):
	exists = False

	for c in cve:
		if c == cveValue:
			exists = True
			break

	return exists


def getCVE(constraintViolations):

	cve = []
	returnCve = "no-cve"

	for constraintViolation in constraintViolations:
		reasons = constraintViolation["reasons"]
		for reason in reasons:
			if reason["reference"]:
				cveValue = reason["reference"]["value"]

				if not cveExists(cve, cveValue):
					cve.append(cveValue)

	if len(cve) == 1:
		returnCve = cve[0]
	elif len(cve) > 1:
		returnCve = "many cves"

	return returnCve


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

						if componentViolation["component"]["packageUrl"] is not None:
							componentName = componentViolation["component"]["packageUrl"]
						else:
							componentName = "no-component-name"

						componentHash = componentViolation["component"]["hash"]
						waivedPolicyViolations = componentViolation["waivedPolicyViolations"]

						for waivedPolicyViolation in waivedPolicyViolations:
							policyName = waivedPolicyViolation["policyName"]
							constraintViolations = waivedPolicyViolation["constraintViolations"]

							if "vulnerabilityId" in waivedPolicyViolation["policyWaiver"].keys():
								vulnerabilityId = waivedPolicyViolation["policyWaiver"]["vulnerabilityId"]
							else:
								vulnerabilityId = getCVE(constraintViolations)

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
	f = open(waiverPayload)
	waivers = json.load(f)

	with open(existingWaiversJson, "w") as wfile:
		json.dump(waivers, wfile, indent=2)

	listWaivers(waivers)

				
if __name__ == '__main__':
	main()
