import threading
import boto3
import aws.utils
from django.http import HttpResponse
import json

# simple metrics collection middleware
def metrics(get_response):
    def middleware(request):
        print "Request received: " + str(request)
        try:
            cw = boto3.client("cloudwatch", aws.utils.myRegion)
            cw.put_metric_data(MetricData=[
                    {
                    'MetricName': 'requests',
                    'Dimensions': [ {'Name':'AutoScalingGroupName', 'Value': aws.utils.myASG} ], 
                    'Unit': 'Count',
                    'Value': 1,
                    'StorageResolution': 1 # high resolution
                    }
                ], Namespace='p12')
        except Exception as ex:
             print "Exception: " + str(ex)
        # forward the request to the next handler
        response = get_response(request)
        return response
    return middleware

mutex = threading.Lock()
#simple rate-limiting middleware
def ratelimit(get_response):
    global inflight
    inflight = 0
    THRESHOLD = 2

    def middleware(request):
        global inflight
        with mutex:
            inflight += 1 
            print inflight
        try:
            if inflight <= THRESHOLD:
                # forward the request to the next handler
                response = get_response(request)
            else:
                response = HttpResponse(json.dumps({"message": "Throttled"}), content_type='application/json', status=503)
        except Exception as ex:
            print "Exception: " + str(ex)
            response = HttpResponse(json.dumps({"error": str(ex)}), content_type='application/json', status=500)
        finally:
            with mutex:
                inflight -= 1
                print inflight

        return response

    return middleware


