import boto3
from datetime import datetime, timedelta
import os

asg = boto3.client('autoscaling')
cw = boto3.client('cloudwatch')

def lambda_handler(event, context):
    """ Lambda handler taking cloud watch events and auto scaling asg. """

    ASG_NAME = os.environ['ASG_NAME']

    asg_resp = asg.describe_auto_scaling_groups(AutoScalingGroupNames=[ASG_NAME])
    print(asg_resp)

    metrics_req=[{
        'Id': 'requests',
        'MetricStat': {
            'Metric': {
                'Namespace': 'p12',
                'MetricName': 'requests',
                'Dimensions': [
                    {
                        'Name': 'AutoScalingGroupName',
                        'Value': ASG_NAME
                    }
                ]
            },
            'Period': 1,
            'Stat': 'Sum',
            'Unit': 'Count', # 'None'? 'Count'? 'Count/Second'?
        },
        'ReturnData': True
    }]

    PERIOD=30
    metrics_resp = cw.get_metric_data(
        MetricDataQueries = metrics_req,
        StartTime = datetime.now()-timedelta(seconds=PERIOD),
        EndTime = datetime.now(),
        ScanBy ='TimestampDescending',
        MaxDatapoints=2
    )
    print(metrics_resp)

    aggregate_rps = 0
    metrics = metrics_resp['MetricDataResults'][0]['Values']
    if len(metrics)>0:
        aggregate_rps = int(metrics[0])
    print("Last aggregate RPS: " + str(aggregate_rps))

    requests_per_instance = 2
    desired_instance_num = aggregate_rps / requests_per_instance
    desired_instance_num = int(desired_instance_num + 0.9)

    min_instance_num = asg_resp['AutoScalingGroups'][0]['MinSize']
    max_instance_num = asg_resp['AutoScalingGroups'][0]['MaxSize']
    instance_num_asg = asg_resp['AutoScalingGroups'][0]['DesiredCapacity']
    cur_instance_num = len(asg_resp['AutoScalingGroups'][0]['Instances'])

    if (desired_instance_num < min_instance_num):
            desired_instance_num = min_instance_num
    if (desired_instance_num > max_instance_num):
            desired_instance_num = max_instance_num

    print("cur_instance_num: ", cur_instance_num)
    print("instance_num_asg: ", instance_num_asg)
    print("desired_instance_num: ", desired_instance_num)

    if (instance_num_asg != desired_instance_num):
        response = asg.update_auto_scaling_group(
            AutoScalingGroupName = ASG_NAME,
            DesiredCapacity = desired_instance_num,
        )

        print("scaled: " + str(response))

    return {"statusCode": 200}
