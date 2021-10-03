import json
import requests
import os
import os.path
import sys
import csv

iqurl = sys.argv[1]
iquser = sys.argv[2]
iqpwd = sys.argv[3]

datadir = "datafiles/"
existingWaiversCsv = "{}{}".format(datadir, "existingWaivers.csv")
applyWaiverCmds = "{}{}".format(datadir, "applyWaiversCmds.txt")

def getNexusIqData(api):
	url = "{}{}" . format(iqurl, api)

	req = requests.get(url, auth=(iquser, iqpwd), verify=False)

	if req.status_code == 200:
		res = req.json()
	else:
		res = "Error fetching data"

	return res


def getCVE(reason):
	cve = "no-cve"
	info = reason.split(' ')

	if len(info) == 11:
		cve = info[3]

	return cve


def getApplicationId(applicationPublicName):
	applicationId = ""

	endPoint = "{}{}" . format("/api/v2/applications?publicId=", applicationPublicName)
	applicationData = getNexusIqData(endPoint)

	if applicationData["applications"]:
		applicationId = applicationData["applications"][0]["id"]

	return applicationId


def getApplicationReport(applicationId, findStage):
	endPoint = "{}{}" . format("/api/v2/reports/applications/", applicationId)
	reportsData = getNexusIqData(endPoint)
	foundreportDataUrl = ""

	for report in reportsData:
		reportStage = report["stage"]
		reportDataUrl = report["reportDataUrl"]

		if reportStage == findStage:
			foundreportDataUrl = reportDataUrl.replace('/raw', '/policy')
			break

	return foundreportDataUrl


def getEvaluationReport(applicationReportUrl):
	reportsData = getNexusIqData("/" + applicationReportUrl)
	return reportsData


def findViolation(evaluation, searchViolation):
	applicationId = evaluation["application"]["id"]
	applicationName = evaluation["application"]["publicId"]
	components = evaluation["components"]
	foundPolicyViolationId = ""

	for component in components:
		packageUrl = component["packageUrl"]

		if not packageUrl:
			packageUrl = "none"

		policyName = ""
		reason = ""

		violations = component['violations']

		for violation in violations:
			policyThreatLevel = violation['policyThreatLevel']
			policyName = violation['policyName']
			policyId = violation['policyId']
			policyThreatCategory = violation['policyThreatCategory']
			policyViolationId = violation['policyViolationId']
			waived = violation['waived']
			foundPolicyViolationId = policyViolationId
			# if waived == "true":
			# 	foundPolicyViolationId = "waived"
			# 	break

			cve = ""

			if  policyThreatCategory == "SECURITY":
				constraints = violation['constraints']
				for constraint in constraints:
					conditions = constraint['conditions']

					for condition in conditions:
						reason = condition['conditionReason']
						cve = getCVE(reason)

					if applicationName == searchViolation["applicationPublicId"] and packageUrl == searchViolation["packageUrl"] and policyName == searchViolation["policyName"] and cve == searchViolation["cve"]:
						# use these fields to find the policyViolationId we need (captured above)
						# if all 4 match fields in searchViolation we have our policyViolationId
						# for the apply waiver API we need applicationPublicId, policyViolationId
						# print (applicationName + " " + packageUrl + " " + policyName + " " + cve + "\n")
						foundPolicyViolationId = policyViolationId
						break


	return foundPolicyViolationId





def getWaiverCmd(policyViolationId, violation):
	applicationEndpoint = "/api/v2/policyWaivers/application/"
	organizationEndpoint = "/api/v2/policyWaivers/organization/"
	waiverComment = "adding waiver"
	# endPoint = ""
	ROOT_ORG = "ROOT_ORGANIZATION_ID"

	applicationPublicId = violation["applicationPublicId"]
	comment = violation["comment"]
	scopeType = violation["scopeType"]
	scopeName = violation["scopeName"]
	scopeOwnerId = violation["scopeOwnerId"]

	if not comment == "":
		waiverComment = "{\"comment\":\"" + comment + "\""


	if scopeType == "root_organization":
		# endPoint = organizationEndpoint
		waiverScopeName = ROOT_ORG
	elif scopeType == "organization":
		# endPoint = organizationEndpoint
		waiverScopeName = scopeOwnerId
	else:
		# endPoint = applicationEndpoint
		waiverScopeName = "/application"

	# cmd = "curl -u " + iquser + ":" + iqpwd + " -X POST -H \"Content-Type: application/json\" -d " + "'{\"comment\": \"" + waiverComment + "\"}' " + iqurl + endPoint + waiverScopeName + "/" + policyViolationId + "\n"
	                   # curl -u admin:admin123 -X POST -H "Content-Type: text/plain; charset=UTF-8" http://nexus-iq-server.sonatype.com:8070/api/v2/policyWaiver/81513a08599a4d399528c6184f0a9200/application --data-binary 'waiver comment (optional)'
	
	if scopeType == "root_organization":
		cmd = "curl -u " + iquser + ":" + iqpwd + " -X POST -H 'Content-Type: application/json' " + iqurl + "/api/v2/policyWaivers/organization/" + ROOT_ORG + "/" + policyViolationId + " -d '" + waiverComment + "}'\n"
	elif scopeType == "organization":
		cmd = "curl -u " + iquser + ":" + iqpwd + " -X POST -H 'Content-Type: application/json' " + iqurl + "/api/v2/policyWaivers/organization/" + scopeOwnerId + "/" + policyViolationId + " -d '" + waiverComment + "}'\n"
	else:
		cmd = "curl -u " + iquser + ":" + iqpwd + " -X POST -H 'Content-Type: text/plain; charset=UTF-8' " + iqurl + "/api/v2/policyWaiver/" + policyViolationId + waiverScopeName + " --data-binary '" + waiverComment + "'" + "\n"
		# cmd = "curl -u " + iquser + ":" + iqpwd + " -X POST -H 'Content-Type: text/plain; charset=UTF-8' " + iqurl + "/api/v2/policyWaivers/application/" + scopeOwnerId + "/" + policyViolationId + " --data-binary '" + waiverComment + "'" + "\n"

	return cmd


def dumpPayload(applicationPublicId, payload):
	payloadFile = datadir + applicationPublicId + ".json"

	if os.path.exists(payloadFile):
		print (payloadFile + ": file already exists. ",end='')
	else:
		print (" dumping evaluation json. ",end='')
		with open(payloadFile, "w") as wfile:
			json.dump(payload, wfile, indent=2)

	return

def main():
	f = open("bcat_bcat-frontend.json")
	bcatEvaluation = json.load(f)

	dumpEvaluation = True
	countWaivers = 0

	with open(applyWaiverCmds, 'w') as fd:
		with open("bcat_existingWaivers.csv") as csvfile:
			csvdata = csv.reader(csvfile, delimiter='\t')
			for v in csvdata:

				violation = {
					"applicationPublicId": v[0],
					"packageUrl": v[1],
					"hash": v[2],
					"policyName": v[3],
					"cve": v[4],
					"stage": v[5],
					"comment": v[6],
					"scopeName": v[7],
					"scopeType": v[8],
					"scopeOwnerId": v[9],

				}

				countWaivers += 1
				print(str(countWaivers) + " checking for: " + violation["applicationPublicId"] + ":" + violation["packageUrl"] + ":" + violation["policyName"] + ". ", end='')


				# applicationId = getApplicationId(violation["applicationPublicId"])
				applicationId = "bcat"

				if (len(applicationId) > 0):

					# applicationReportUrl = getApplicationReport(applicationId, violation["stage"])
					# evaluation = getEvaluationReport(applicationReportUrl)
					evaluation = bcatEvaluation

					if dumpEvaluation:
						dumpPayload(violation["applicationPublicId"], evaluation)

					if  violation["cve"] == "no-cve":
						print (" no-cve: " + violation["applicationPublicId"] + ":" + violation["packageUrl"] + ":" + violation["policyName"])
						continue

					policyViolationId = findViolation(evaluation, violation)

					# if policyViolationId == "waived":
					# 	print (" is waived")
					# else:
					# 	print (" writing waiver command")
					# 	waiverComd = getWaiverCmd(policyViolationId, violation)
					# 	fd.write(waiverComd)

					print (" writing waiver command")
					waiverComd = getWaiverCmd(policyViolationId, violation)
					fd.write(waiverComd)

				else:
					print (" application not found: " + violation["applicationPublicId"])

			print("\n")


if __name__ == '__main__':
	main()
