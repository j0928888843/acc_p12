From python:2-slim
RUN apt-get update && apt-get install -y wget curl
RUN pip install --upgrade django==1.11 requests boto3
COPY packages /home/ubuntu/packages
WORKDIR /home/ubuntu/
RUN wget --quiet https://s3.amazonaws.com/glikson-public/DLL/packages/packages.tar.gz -O - | tar -C packages -xz 
RUN wget --quiet https://s3.amazonaws.com/glikson-public/DLL/model/model_197x197.hdf5 -O /tmp/model.hdf5
COPY . /home/ubuntu/
EXPOSE 80

CMD python -u webapp/manage.py runserver 0.0.0.0:80
