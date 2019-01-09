# 15719: Starter code for Project 1 - Part 2

Please, follow instructions instructions at [TheProject.Zone](https://theproject.zone/s19-advcc/autoscaling-controller) to develop a custom auto-scaling controller that meets project requirements.

## Web Service - Application
### Build Application Image
```
$ REPO="719p12"
$ TAG="latest"
$ IMAGE=$REPO:$TAG
$ docker build -t $IMAGE webservice/
```

### Upload to EC2 Container Registry (ECR)
```
$ REGION="us-east-1"
$ aws configure set region $REGION
$ $(aws ecr get-login --no-include-email)
# The following command creates an image repository called "719p12". You need to do it just once.
$ aws ecr create-repository --repository-name $REPO
$ REGISTRY=$(aws ecr describe-repositories --repository-names $REPO | jq -r .repositories[0].registryId)
$ REGISTRYURL=$REGISTRY.dkr.ecr.$REGION.amazonaws.com
$ docker tag $IMAGE $REGISTRYURL/$IMAGE
$ docker push $REGISTRYURL/$IMAGE
```

### Run and test the container locally
```
# if you did not push the image to ECR, skip the following command
$ docker pull $REGISTRYURL/$IMAGE
$ export AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
$ export AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id)
$ export AWS_ASG_NAME="myasg"
$ docker run -d -p 8080:80 -e AWS_SECRET_ACCESS_KEY -e AWS_ACCESS_KEY_ID -e AWS_ASG_NAME --name p12 $IMAGE
# Test
$ curl http://localhost:8080/predict?image=https://fido.imgix.net/wp/2013/11/cute-puppy.jpg
$ docker logs p12
# Cleanup
$ docker rm -f p12
$ docker system prune -f
```
### Deploy Web Service and Controller
The EC2 instances comprising the Web Service will automatically pull the application image from ECR.
```
$ terraform init
$ terraform apply
$ ALB_URL=$(terraform output load-balancer-dns)
```
## Test End-to-End
```
$ loadtest -c 5 --rps 9 -t 300 http://${ALB_URL}/dev/predict
```
## Pulling starter updates
1. Add the student common starter code repository as a remote (needs to be done only once):
    ```
    $ git remote add starter git@github.com:cmu15719/p1.2-starter.git
    ```
1. Check if there are pending changes:
    ```
    $ git fetch starter
    $ git log master..starter/master
    ```
    If the output is not empty - there are pending changes you need to pull.
1. Pull from the student common starter code repository:
    ```
    $ git pull starter/master master
    ```
1. Resolve potential conflicts by merging

