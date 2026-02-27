## manage-waivers


#### list-existing-waivers.py 
```python3 list-waivers.py http://localhost:8070 admin admin123```
- this to run on the old instance
- creates a csv file (waiverlist.csv) with one line per waiver

#### get-waiver-cmds.py
```python3 get-waiver-cmds.py http://localhost:8070 admin admin123```
- reads each line from waiverlist.csv above
- finds the corresponding scan report in the new IQ instance (by app name, component, policy name, cve)
- on found, gets the policyViolationId
- shows waiver command using app name and policyViolationId



