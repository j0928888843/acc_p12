# provider "aws" {
#   profile = "default"
#   region = "us-east-1"
# }

locals {
  # common tags applied to all resources
  common_tags = {
    Project = "15719.p1"
  }
}

data "aws_region" "current" {}

resource "aws_default_vpc" "default" {
  tags {
    Name = "Default VPC"
  }
}

resource "aws_default_subnet" "default_az1" {
  availability_zone = "${data.aws_region.current.id}a"

  tags {
    Name = "Default subnet for ${data.aws_region.current.id}a"
  }
}

resource "aws_default_subnet" "default_az2" {
  availability_zone = "${data.aws_region.current.id}b"

  tags {
    Name = "Default subnet for ${data.aws_region.current.id}b"
  }
}

// security group for lb and asg
resource "aws_security_group" "security-group-alb-asg" {
  name        = "p12-sg-alb-asg"
  description = "Security Group for Application Load Balancer and Auto Scaling Group"
  vpc_id      = "${aws_default_vpc.default.id}"

  tags = "${merge(
    local.common_tags
  )}"

  # SSH access from anywhere (for TAs)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP access from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Heartbeat access from anywhere
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

data "aws_ami" "p12-ami" {
  most_recent = true
  filter {
    name   = "name"
    values = ["cmu-advcc-p12"]
  }
}

# IAM role attached to the launch configuration. This governs what resources our
# web service ec2 instances has access to
resource "aws_iam_role" "role-for-ec2" {
  name = "p12-role-for-ec2"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

# Create a AMI policy to allowed lambda to access all EC2 resources
resource "aws_iam_policy" "ec2-iam-policy" {
  name        = "p12-ec2-iam-policy"
  description = "p12-ec2-iam-policy"

  #This policy:
  #Allows ec2 instance to have full access to CloudWatch
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "autoscaling:Describe*",
                "cloudwatch:*",
                "logs:*",
                "sns:*",
                "ecr:*",
                "iam:GetPolicy",
                "iam:GetPolicyVersion",
                "iam:GetRole"
            ],
            "Effect": "Allow",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "iam:CreateServiceLinkedRole",
            "Resource": "arn:aws:iam::*:role/aws-service-role/events.amazonaws.com/AWSServiceRoleForCloudWatchEvents*",
            "Condition": {
                "StringLike": {
                    "iam:AWSServiceName": "events.amazonaws.com"
                }
            }
        }
    ]
}
EOF
}

# Attach the AMI policy to the AMI role for ec2.
resource "aws_iam_role_policy_attachment" "ec2-policy-attach" {
  role       = "${aws_iam_role.role-for-ec2.name}"
  policy_arn = "${aws_iam_policy.ec2-iam-policy.arn}"
}

resource "aws_iam_instance_profile" "profile-for-ec2" {
  name = "p12-profile-for-ec2"
  role = "${aws_iam_role.role-for-ec2.name}"
}

resource "aws_launch_configuration" "launch-config" {
  name = "p12-launch-config"
  image_id             = "${data.aws_ami.p12-ami.id}"
  instance_type        = "t2.small"
  security_groups      = ["${aws_security_group.security-group-alb-asg.name}"]
  iam_instance_profile = "${aws_iam_instance_profile.profile-for-ec2.name}"
}

resource "aws_alb_target_group" "target-group-ws" {
  name                 = "p12-target-group-ws"
  port                 = "80"
  protocol             = "HTTP"
  vpc_id               = "${aws_default_vpc.default.id}"
  slow_start           = 0                               // Do not wait for the server to warm up.
  deregistration_delay = 5                               // Terminate instance 5s after deregistreted.

  health_check {
    protocol = "HTTP"
    timeout  = 5
    interval = 30
    path     = "/"
    port     = 80
  }

  tags = "${merge(
    local.common_tags
  )}"
}

resource "aws_alb_target_group" "target-group-admin" {
  name                 = "p12-target-group-admin"
  port                 = "8080"
  protocol             = "HTTP"
  vpc_id               = "${aws_default_vpc.default.id}"
  slow_start           = 0                               // Do not wait for the server to warm up.
  deregistration_delay = 5                               // Terminate instance 5s after deregistreted.

  health_check {
    protocol = "HTTP"
    interval = 30
    path     = "/"
    port     = 8080
  }

  tags = "${merge(
    local.common_tags
  )}"
}

resource "aws_alb" "alb" {
  name               = "p12-alb"
  load_balancer_type = "application"
  security_groups    = ["${aws_security_group.security-group-alb-asg.id}"]

  subnets = ["${aws_default_subnet.default_az1.id}", "${aws_default_subnet.default_az2.id}"]

  tags = "${merge(
    local.common_tags
  )}"
}

resource "aws_lb_listener" "alb_listener_ws" {
  load_balancer_arn = "${aws_alb.alb.arn}"
  port              = "80"
  protocol          = "HTTP"

  default_action {
    target_group_arn = "${aws_alb_target_group.target-group-ws.arn}"
    type             = "forward"
  }
}

resource "aws_lb_listener" "alb_listener_admin" {
  load_balancer_arn = "${aws_alb.alb.arn}"
  port              = "8080"
  protocol          = "HTTP"

  default_action {
    target_group_arn = "${aws_alb_target_group.target-group-admin.arn}"
    type             = "forward"
  }
}

resource "aws_autoscaling_group" "asg" {
  name                      = "p12-asg"
  availability_zones        = ["${aws_default_subnet.default_az1.availability_zone}"]
  min_size                  = 1
  max_size                  = 10
  desired_capacity          = 1
  enabled_metrics           = ["GroupDesiredCapacity", "GroupInServiceInstances", "GroupPendingInstances", "GroupStandbyInstances", "GroupTerminatingInstances", "GroupTotalInstances"]
  health_check_type         = "ELB"
  health_check_grace_period = 30
  default_cooldown          = 5

  launch_configuration = "${aws_launch_configuration.launch-config.name}"
  target_group_arns    = ["${aws_alb_target_group.target-group-ws.arn}", "${aws_alb_target_group.target-group-admin.arn}"]

  tags = [
    {
      key                 = "Project"
      value               = "15719.p1"
      propagate_at_launch = true
    },
  ]
}

# output load-balancer-dns
output "load-balancer-dns" {
  value = "${aws_alb.alb.dns_name}"
}

# output asg-name for controller deployment
output "asg_name" {
  value = "${aws_autoscaling_group.asg.name}"
}
