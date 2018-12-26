# provider "aws" {
#   region = "us-east-1"
# }

locals {
  # common tags applied to all resources
  common_tags = {
    Project = "15719.p1"
  }
}

variable "asg_name" {
  type    = "string"
}

data "aws_region" "current" {}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "scale-lambda" {
  filename         = "${path.module}/lambda.zip"
  function_name    = "p12-scale"
  role             = "${aws_iam_role.role-for-lambda.arn}"
  handler          = "lambda.lambda_handler"
  runtime          = "python3.6"
  source_code_hash = "${data.archive_file.lambda_zip.output_base64sha256}"
  timeout          = 15

  environment {
    variables = {
      ASG_NAME    = "${var.asg_name}"
    }
  }

  tags = "${merge(
    local.common_tags
  )}"
}

# IAM role attached to the Lambda Function. This governs what resources our
# Lambda Function has access to
resource "aws_iam_role" "role-for-lambda" {
  name = "p12-role-for-lambda"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

# Create a AMI policy to allowed lambda to access all EC2 resources
resource "aws_iam_policy" "lambda-iam-policy" {
  name        = "p12-lambda-iam-policy"
  description = "lambda-iam-policy"

  #This policy:
  #allow CloudWatch to create LogGroup for lambda (convenient to debug)
  #allow lambda to access autoscaling resources.
  #TODO: finer grained access control

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Action": [
        "autoscaling:*"
      ],
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Action": [
        "cloudwatch:*"
      ],
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Action": [
        "lambda:*"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
EOF
}

# Attach the AMI policy to the AMI role for lambda.
resource "aws_iam_role_policy_attachment" "lambda-policy-attach" {
  role       = "${aws_iam_role.role-for-lambda.name}"
  policy_arn = "${aws_iam_policy.lambda-iam-policy.arn}"
}

# IAM role attached to the step function. This governs what resources our
# step function has access to
resource "aws_iam_role" "role-for-sfn" {
  name = "p12-role-for-sfn"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "states.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

# Create a AMI policy to allowed step function to access lambda functions
resource "aws_iam_policy" "sfn-iam-policy" {
  name        = "p12-sfn-iam-policy"
  description = "sfn-iam-policy"

  #This policy:
  #allow step function to invoke lambda function.

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:InvokeFunction"
            ],
            "Resource": [
                "*"
            ]
        }
    ]
}
EOF
}

# Attach the AMI policy to the AMI role for step function.
resource "aws_iam_role_policy_attachment" "sfn-policy-attach" {
  role       = "${aws_iam_role.role-for-sfn.name}"
  policy_arn = "${aws_iam_policy.sfn-iam-policy.arn}"
}

# Create an AWS step function to trigger lambda controller periodically
resource "aws_sfn_state_machine" "lambda-state-machine" {
  name     = "p12-lambda-state-machine"
  role_arn = "${aws_iam_role.role-for-sfn.arn}"

  definition = <<EOF
{
  "StartAt": "lambda",
  "States": {
    "lambda": {
      "Type": "Task",
      "Resource": "${aws_lambda_function.scale-lambda.arn}",
      "ResultPath": "$",
      "Next": "choice"
    },
    "choice": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.statusCode",
          "NumericEquals": 410,
          "Next": "gone"
        }
      ],
      "Default": "wait"
    },
    "wait": {
      "Type": "Wait",
      "Seconds": 30,
      "Next": "lambda"
    },
    "gone": {
      "Type": "Fail",
      "Cause": "Lambda need to be purged."
    }
  }
}
EOF
}

# a random string to trigger the null resource
resource "random_string" "random_string" {
  length  = 16
  special = true
}

# A null resource to invoke step function when "terraform apply"
resource "null_resource" "exec-lambda" {
  triggers {
    random_string = "${random_string.random_string.result}"
  }

  provisioner "local-exec" {
    command = "aws stepfunctions start-execution --state-machine-arn ${aws_sfn_state_machine.lambda-state-machine.id}"
  }

  # we must specify dependency here so that we invoke lambda after it is created.
  depends_on = ["aws_sfn_state_machine.lambda-state-machine", "aws_lambda_function.scale-lambda"]
}
