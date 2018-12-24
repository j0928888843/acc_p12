import os
import requests

def __get_region():
    try:
        doc = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document").json()
        if "region" in doc:
            return doc["region"]
        return None
    except:
        return None

AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_ASG_NAME = os.getenv("AWS_ASG_NAME", "asg")
AWS_REGION = os.getenv("AWS_REGION", __get_region() or "us-east-1")

