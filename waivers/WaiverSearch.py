import requests
import json

resp = requests.get('http://localhost:8070/api/v2/reports/components/waivers', auth=('admin','admin123'))
if resp.status_code != 200:
    # This means something went wrong.
    raise ApiError('GET /tasks/ {}'.format(resp.status_code))

else:
	data = json.loads(resp.text)
	applicationWaivers = data["applicationWaivers"]
	compSearch = raw_input("Enter the component you want to search for...").lower()
	for (k, v) in data.items():
		if k == "applicationWaivers":
			for a in v:
				app_name = a["application"]["name"]
      			print("____________________________________________________________________________________")
      			print(app_name)
      			print("____________________________________________________________________________________")
      			for stage in a["stages"]:
      				print("Stage: "+stage["stageId"])
      				print("____________________________________________________________________________________")
      				for componentPolicyViolations in stage["componentPolicyViolations"]:
						components = componentPolicyViolations["component"]
						if compSearch is "" or compSearch in components["packageUrl"]:
							waivers = componentPolicyViolations["waivedPolicyViolations"]
							print("Component name and version: ")
							print(components["packageUrl"])
							for waiver in waivers:
								print("Waiver type: "+waiver["policyName"]+"\n")
								print("---------------------------------------I N F O--------------------------------------\n")
								print("policyWaiverId:"+waiver["policyWaiver"]["policyWaiverId"])
								print("Time Created:"+waiver["policyWaiver"]["createTime"])
								print("Comment:"+waiver["policyWaiver"]["comment"])
								print("scopeOwnerName:"+waiver["policyWaiver"]["scopeOwnerName"])
								print("____________________________________________________________________________________")

