import json
import requests
import os
import os.path
import sys
import csv

iqurl = sys.argv[1]
iquser = sys.argv[2]
iqpwd = sys.argv[3]

datadir = "datafiles"
existingWaiversCsv = "{}/{}".format(datadir, "existingWaivers.csv")
applyWaiverCmds = "{}/{}".format(datadir, "applyWaiversCmds.txt")

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
	endPoint = ""
	ROOT_ORG = "ROOT_ORGANIZATION_ID"

	applicationPublicId = violation["applicationPublicId"]
	comment = violation["comment"]
	scopeType = violation["scopeType"]
	scopeName = violation["scopeName"]

	if not comment == "":
		waiverComment = comment

	if scopeType == "root_organization":
		endPoint = organizationEndpoint
		waiverScopeName = ROOT_ORG
	elif scopeType == "organization":
		endPoint = organizationEndpoint
		waiverScopeName = scopeName
	else:
		endPoint = applicationEndpoint
		waiverScopeName = scopeName


	cmd = "curl -u " + iquser + ":" + iqpwd + " -X POST -H \"Content-Type: application/json\" -d " + "'{\"comment\": \"" + waiverComment + "\"}' " + iqurl + endPoint + waiverScopeName + "/" + policyViolationId + "\n"
	return cmd


def main():

	countWaivers = 0
	with open(applyWaiverCmds, 'w') as fd:
		with open(existingWaiversCsv) as csvfile:
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
					"scopeTyId": v[9],

				}
				countWaivers += 1
				print(str(countWaivers) + " checking for: " + violation["applicationPublicId"])

				applicationId = getApplicationId(violation["applicationPublicId"])

				if (len(applicationId) > 0):
					applicationReportUrl = getApplicationReport(applicationId, violation["stage"])
					evaluation = getEvaluationReport(applicationReportUrl)
					policyViolationId = findViolation(evaluation, violation)

					if  violation["cve"] == "no-cve":
						print ("no-cve: " + violation["applicationPublicId"] + ":" + violation["packageUrl"] + ":" + violation["policyName"])
						continue

					waiverComd = getWaiverCmd(policyViolationId, violation)
					fd.write(waiverComd)


if __name__ == '__main__':
	main()
