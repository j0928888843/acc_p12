# 15719: Starter code for Poroject 1 - Part 2
## Web Service - Application
### Build Application Image
```
$ REPO="719p12"
$ TAG="latest"
$ IMAGE=$REPO:$TAG
$ docker build -t $IMAGE app/
```

### Upload to EC2 Container Registry (ECR)
```
$ REGION="us-east-1"
$ aws configure set region $REGION
$ $(aws ecr get-login --no-include-email)
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
$ loadtest -c 5 --rps 9 -t 300 http://${ALB_URL}/predict
```

