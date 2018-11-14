# 719-p1.2-starter
## Example Usage
```
$ docker build -t p12starter .
$ docker run -d -p 8080:8080 p12starter
$ curl http://localhost:8080/predict?images=https://s3.amazonaws.com/glikson-public/DLL/data/inf5.tgz
```
