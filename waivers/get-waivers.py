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


def getPolicyIds(data):
	policyIds = ""
	policies = data['policies']

	for policy in policies:
		name = policy["name"]
		id = policy["id"]

		if name == "Security-Critical" or name == "Security-High" or name == "Security-Medium" or name == "License-Banned" or name == "License-None" or name == "License-Copyleft":
			policyIds += "p=" + id + "&"

	result = policyIds.rstrip('&')

	return result


def listWaivers(waivers):

	applicationWaivers = waivers['applicationWaivers']

	with open('componentWaivers.csv', 'w') as fd:
			for waiver in applicationWaivers:
				applicationPublicId = waiver["application"]["publicId"]

				stages = waiver["stages"]

				for stage in stages:
					stageId = stage["stageId"]
					componentPolicyViolations = stage["componentPolicyViolations"]

					for componentViolation in componentPolicyViolations:
						componentName = componentViolation["component"]["packageUrl"]
						waivedPolicyViolations = componentViolation["waivedPolicyViolations"]

						for waivedPolicyViolation in waivedPolicyViolations:
							policyName = waivedPolicyViolation["policyName"]
							vulnerabilityId = waivedPolicyViolation["policyWaiver"]["vulnerabilityId"]
							comment = waivedPolicyViolation["policyWaiver"]["comment"]

							line = applicationPublicId + "," + componentName + "," + policyName + "," + vulnerabilityId + "," + stageId + "," + comment + "\n"
							print(line)
							fd.write(line)

	print('componentWaivers.csv')
	return


def main():
	waivers = getNexusIqData('/api/v2/reports/components/waivers')
	listWaivers(waivers)
	# waiversfmt = json.dumps(waivers, indent=2)
	# print(waiversfmt)

				
if __name__ == '__main__':
	main()
