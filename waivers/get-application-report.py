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


def getCVE(reason):
	cve = "no-cve"
	info = reason.split(' ')

	if len(info) == 11:
		cve = info[3]

	return cve


def getApplicationId(applicationPublicName):
	endPoint = "{}{}" . format("/api/v2/applications?publicId=", applicationPublicName)
	applicationData = getNexusIqData(endPoint)
	applicationId = applicationData["applications"][0]["id"]
	return applicationId


def getApplicationReports(applicationId, findStage):
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

					print (applicationName + " " + packageUrl + " " + policyName + " " + cve + "\n")

	return


def main():

	violation = {
		"applicationPublicId": "p1",
		"packageUrl": "pkg:pypi/confire@0.2.0?extension=tar.gz",
		"policyName": "Security-Critical",
		"cve": "CVE-2017-16763",
		"stage": "build"
	}

	applicationId = getApplicationId(violation["applicationPublicId"])
	applicationReportUrl = getApplicationReports(applicationId, violation["stage"])
	evaluation = getEvaluationReport(applicationReportUrl)
	findViolation(evaluation, violation)


	# waiversfmt = json.dumps(waivers, indent=2)
	# print(waiversfmt)

				
if __name__ == '__main__':
	main()
