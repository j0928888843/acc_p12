import boto3
from datetime import datetime, timedelta
import os

asg = boto3.client('autoscaling')
cw = boto3.client('cloudwatch')


def lambda_handler(event, context):
    """ Lambda handler taking cloud watch events and auto scaling asg. """

    ASG_NAME = os.environ['ASG_NAME']

    asg_resp = asg.describe_auto_scaling_groups(
        AutoScalingGroupNames=[ASG_NAME])
    print(asg_resp)

    metrics_req = [{
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
            'Period': 5,  # old:1, need to be [1,5,10,30], sum interval
            'Stat': 'Sum',
            'Unit': 'Count',
        },
        'ReturnData': True
    }]

    PERIOD = 70  # this is oberserv time
    metrics_resp = cw.get_metric_data(
        MetricDataQueries=metrics_req,
        StartTime=datetime.now() - timedelta(seconds=PERIOD),
        EndTime=datetime.now(),
        ScanBy='TimestampDescending',
        # The maximum number of data points the request should return before
        # paginating.the default of 100,800 is used.
        MaxDatapoints=6
    )
    print(metrics_resp)

    aggregate_rps = 0
    metrics = metrics_resp['MetricDataResults'][0]['Values']
    if len(metrics) > 1:
        # add /5 since we increas period to 5
        aggregate_rps = int(metrics[1]) / 5  # [1] is more accurate
    print("Last aggregate RPS: " + str(aggregate_rps))

    # set margin and idea requests_per_instance
    margin = 0.7
    requests_per_instance = 2.4

    desired_instance_num = aggregate_rps / requests_per_instance
    desired_instance_num = int(desired_instance_num + margin)

    # add previous aggregate_rps
    prev_aggregate_rps = 0
    if len(metrics) > 2:
        prev_aggregate_rps = int(metrics[2]) / 5  # [2] is [1]'s prev
    print("prev aggregate RPS: " + str(prev_aggregate_rps))

    prev_desired_instance_num = prev_aggregate_rps / requests_per_instance
    prev_desired_instance_num = int(prev_desired_instance_num + margin)

    # add previous2 aggregate_rps
    prev2_aggregate_rps = 0
    if len(metrics) > 3:
        prev2_aggregate_rps = int(metrics[3]) / 5  # [3] is [2]'s prev
    print("prev2 aggregate RPS: " + str(prev2_aggregate_rps))

    prev2_desired_instance_num = prev2_aggregate_rps / requests_per_instance
    prev2_desired_instance_num = int(prev2_desired_instance_num + margin)

    if (desired_instance_num == prev_desired_instance_num) and (prev_desired_instance_num == prev2_desired_instance_num):
        flag = 1
    else:
        flag = 0

    print("flag: " + str(flag))

    min_instance_num = asg_resp['AutoScalingGroups'][0]['MinSize']
    max_instance_num = asg_resp['AutoScalingGroups'][0]['MaxSize']
    instance_num_asg = asg_resp['AutoScalingGroups'][0]['DesiredCapacity']
    cur_instance_num = len(asg_resp['AutoScalingGroups'][0]['Instances'])

    if (desired_instance_num < min_instance_num):
        desired_instance_num = min_instance_num
    if (desired_instance_num > max_instance_num):
        desired_instance_num = max_instance_num

    print("cur_instance_num: ", cur_instance_num)
    print("current DesiredCapacity: ", instance_num_asg)

    if (instance_num_asg != desired_instance_num) and (flag == 1):
        response = asg.update_auto_scaling_group(
            AutoScalingGroupName=ASG_NAME,
            DesiredCapacity=desired_instance_num,
        )
        print("DesiredCapacity change to: ", desired_instance_num)
        print("scaled: " + str(response))
    else:
        print("DesiredCapacity is same as: ", instance_num_asg)

    return {"statusCode": 200}
