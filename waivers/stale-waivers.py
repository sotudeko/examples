#!/usr/bin/env python

import json
import requests
from pprint import pprint

input_comp_name = 'angular'
stage_id = "build"

uri = str("localhost")
port = str(8070)
username = "admin"
password = "admin123"
ecosystem = "a-name"


def obtain_stale_waivers():
    theurl_waivers = 'http://localhost:8070/api/v2/reports/waivers/stale'
    # fetch report from uri
    waiver_details = requests.get(theurl_waivers, auth=(username, password))
    # print(res_comp_details)
    # Load result string to json
    json_data_waivers = json.loads(waiver_details.text)
    # print(json.dumps(json_data_waivers, indent=4, sort_keys=True))
    for staleWaiver in json_data_waivers['staleWaivers']:
        print(json.dumps(staleWaiver, indent=4, sort_keys=True))
        #print(waiver['application']['name'])
        #for staleWaiver in (waivers['staleWaivers']):
        #    for comp in comp_violation['componentPolicyViolations']:
        #        comp_format = comp['component']['componentIdentifier']['format']
        #        if comp_format == ecosystem :
        #            print(json.dumps(waiver, indent=4, sort_keys=True))
                    #comp_version =(comp['component']['componentIdentifier']['coordinates']['name'])
                    #comp_name = (comp['component']['componentIdentifier']['coordinates']['version'])
                    #comp_hash = (comp['component']['hash'])
                    #iq_app_name = (waiver['application']['name'])
                    #print(json.dumps(comp, indent=4, sort_keys=True))
                    #print(json.dumps(waiver['application'], indent=4, sort_keys=True))
                    #for stage in waiver['stages']:
                    #    for compPolicyViolation in stage['componentPolicyViolations']:
                    #        print(json.dumps(compPolicyViolation, indent=4, sort_keys=True))
                    #        #for waiverPolicyViolation in compPolicyViolation['waivedPolicyViolations']:
                    #        #    print(json.dumps(waiverPolicyViolation['policyName'], indent=4, sort_keys=True))
                    #        #    print(json.dumps(waiverPolicyViolation['policyWaiver'], indent=4, sort_keys=True))
                    #        #for constraintViolation in waiverPolicyViolation['constraintViolations']:
                    #        #    print(json.dumps(constraintViolation, indent=4, sort_keys=True))


if __name__ == "__main__":
    print(" ")
    print("This is a list of all reports for all IQ waivers associated with "+ecosystem+" identified components")
    print("---------------------------------------------------------------------------------------------")
    obtain_stale_waivers()




