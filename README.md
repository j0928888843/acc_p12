# 719-p1.2-starter
## Example Usage
```
$ sudo docker build -t p12starter .
$ sudo docker run -d -p 8080:8080 -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} --name p12 p12starter
$ curl http://localhost:8080/predict?image=https://fido.imgix.net/wp/2013/11/cute-puppy.jpg
```
## Cleanup
```
$ sudo docker rm -f p12
$ sudo docker system prune -f
```
