From python:2-slim
RUN apt-get update && apt-get install -y wget curl
RUN pip install --upgrade django==1.11 requests
COPY . /home/ubuntu/
WORKDIR /home/ubuntu/
RUN wget --quiet https://s3.amazonaws.com/glikson-public/DLL/packages/packages.tar.gz -O - | tar -C packages -xz 
RUN wget --quiet https://s3.amazonaws.com/glikson-public/DLL/model/model_197x197.hdf5 -O /tmp/model.hdf5
ENV MODEL "https://s3.amazonaws.com/glikson-public/DLL/model/model_197x197.hdf5"
EXPOSE 8080

CMD python -u manage.py runserver 0.0.0.0:8080
