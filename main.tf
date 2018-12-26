provider "aws" {
  region = "us-east-1"
}

module "ws" {
  source = "./ws"
}

module "controller" {
  source = "./controller"
  asg_name = "${module.ws.asg_name}"
}

output "load-balancer-dns" {
   value = "${module.ws.load-balancer-dns}"
}
