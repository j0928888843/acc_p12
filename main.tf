provider "aws" {
  region = "us-east-1"
}

module "webservice" {
  source = "./webservice"
}

module "controller" {
  source = "./controller"
  asg_name = "${module.webservice.asg_name}"
}

output "load-balancer-dns" {
   value = "${module.webservice.load-balancer-dns}"
}
