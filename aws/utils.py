import requests

myRegion = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document").json()['region']
myInstanceId = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document").json()['instanceId']
myASG = 'asg' #TODO retrieve dynamically from AWS API
