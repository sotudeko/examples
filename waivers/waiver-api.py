#!/usr/bin/env python

import json
import requests
from pprint import pprint
import subprocess
import os
import ast


# get the internal IA app ID based on human readable input - DONE
# obtain the hash of the required component - DONE
# obtain report ID for application - DONE
# get policy policythreats.json based on the obtained hash - DONE
# Get policy ID from human readable policy input - DONE
# parse through to get the correct constraintFactsJson - DONE
# construct the create waiver api call and submit to IQ _ DONE

human_app_id = "Core Banking"
human_group_id = "commons-collections"
human_artifact_id = "*"
human_version = "3.2.1"
human_extension = "jar"
human_classifier = "*"
human_stage_id = "build"
human_comment = "Ryan Comment1"

uri = str("localhost")
port = str(8070)
username = "admin"
password = "admin123"

def get_internal_id(human_app_id):

    the_app_url = "http://%s:%s/api/v2/applications/" % (uri, port)
    # fetch report from uri
    res = requests.get(the_app_url, auth=(username, password))

    # Load result string to json
    json_data = json.loads(res.text)
    #pprint(json_data)

    for applications in json_data['applications']:
        iq_int_app_id = str(applications['publicId'])
        iq_human_app_id = str(applications['name'])
        iq_int_app_hash_id = str(applications['id'])

        if iq_human_app_id == human_app_id:


            print("The IQ internal ID for " + str(iq_human_app_id) + " is: " + str(iq_int_app_id)\
                  + "the int hash is : " + str(iq_int_app_hash_id))

            return iq_int_app_id, iq_int_app_hash_id

iq_int_app_id, iq_int_app_hash = get_internal_id(human_app_id)

print("Trying global variables from a tuple, print the app hash ID again" + str(iq_int_app_hash))

def obtain_hash():
    theurl_comps = "http://%s:%s/api/v2/search/component?stageId=" % (uri,port) + human_stage_id + \
    '&componentIdentifier=%7B%22format%22%3A%22maven%22%2C%22coordinates' \
    + '%22%3A%7B%22groupId%22%3A%22'+ str(human_group_id)\
    + '%22%2C%22artifactId%22%3A%22' + str(human_artifact_id)\
    + '%22%2C%22version%22%3A%22' + str(human_version)\
    + '%22%2C%22extension%22%3A%22' + str(human_extension)\
    + '%22%2C%22classifier%22%3A%22' + str(human_classifier)\
    + '%22%7D%7D'
    #print(theurl_comps)
    # fetch report from uri
    res_comp_details = requests.get(theurl_comps, auth=(username, password))
    #print(res_comp_details)
    # Load result string to json
    json_data = json.loads(res_comp_details.text)
    count = 0
    #pprint(json_data)
    for results in json_data['results']:
        count = count + 1
        if count == 1 :
            iq_group_id = str(results['componentIdentifier']['coordinates']['artifactId'])
            iq_artifact_id = str(results['componentIdentifier']['coordinates']['artifactId'])
            iq_version = str(results['componentIdentifier']['coordinates']['version'])
            hash_id = str(results['hash'])

            print("The hash id for " + str(iq_group_id) + ":" + str(iq_artifact_id) \
                  + ":" + str(iq_version) + " is " + str(hash_id))
            return hash_id


def obtain_report_id(iq_int_app_hash):
    print(iq_int_app_hash)
    the_rep_url = "http://" + str(uri) + ":" + str(port) + "/api/v2/reports/applications/" + str(iq_int_app_hash)
    print(the_rep_url)
    # fetch report from uri
    res_reps = requests.get(the_rep_url, auth=(username, password))

    # Load result string to json
    json_data_reps = json.loads(res_reps.text)
    #pprint(json_data_reps)
    for x in json_data_reps:
        iq_stage_id = str(x['stage'])
        iq_report_data_url = str(x['reportDataUrl'])
        if iq_stage_id == human_stage_id:
            y = (iq_report_data_url.split('/'))
            iq_report_id =(y[5])
            print("The report of for application " + human_app_id + " at stage " + str(human_stage_id) + " is " \
                    + str(iq_report_id))
            return iq_report_id

iq_report_id = obtain_report_id(iq_int_app_hash)


def get_policy_violations(iq_report_id, hash_id):
    policy_violations_url = "http://" + str(uri) + ":" + str(port) + "/rest/report/" + str(
        iq_int_app_id) + "/" + \
                            str(iq_report_id) + "/browseReport/policythreats.json"
    print(policy_violations_url)
    res_policy_violations = requests.get(policy_violations_url, auth=(username, password))
    # Load result string to json
    json_data_policy_violations = json.loads(res_policy_violations.text)
    pprint(json_data_policy_violations)
    for component in json_data_policy_violations['aaData']:
        if component['hash'] == hash_id:
            data['hash'] = (component['hash'])
            #print(component['activeViolations'])
            for c in component['activeViolations']:
                data['policyId'] = (c['policyId'])
                data['ownerId'] = str(iq_int_app_id)
                data['constraintFactsJson'] = (c['constraintFactsJson'])
                data['comment'] = str(human_comment)

            #pprint(data)
            return data

def apply_waiver(data, iq_int_app_id):
    waiver_url= "http://" + str(uri) + ":" + str(port) + "/rest/policyWaiver/application/" + str(iq_int_app_id) +"?timestamp=1546252989786"
    print(waiver_url)
    headers = {"Content-Type": "application/json;charset=UTF-8"}
    res_apply_waiver = requests.post(waiver_url, json=data, auth=(username,password), headers=headers)
    print("The return code fomr the api call is " + str(res_apply_waiver.status_code))


def reevaluate_report(iq_int_report_id, iq_int_app_id):
    re_eval_url = "http://localhost:8070/rest/report/" + str(iq_int_app_id) + "/" + str(iq_int_report_id) + "/reevaluatePolicy"
    print(re_eval_url)
    res_re_eval = requests.post(re_eval_url, json=data, auth=(username, password))
    print("The return code from the re-evaluate api call is " + str(res_re_eval.status_code))


if __name__ == "__main__":
    data = {}
    #get_internal_id(human_app_id)
    hash_id = obtain_hash()
    #obtain_report_id(iq_int_app_hash)

    get_policy_violations(iq_report_id, hash_id)
    apply_waiver(data, iq_int_app_id)
    reevaluate_report(iq_report_id, iq_int_app_id)

