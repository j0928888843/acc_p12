From ubuntu:16.04

#ENV LC_ALL "en_US.UTF-8"
#ENV LC_CTYPE "en_US.UTF-8"
RUN apt-get update -y && apt-get install wget curl python-pip -y && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade django==1.11 requests
COPY . /home/ubuntu/
WORKDIR /home/ubuntu/
RUN wget https://s3.amazonaws.com/glikson-public/DLL/packages/packages.tar.gz -O - | tar -C packages -xz 
RUN wget https://s3.amazonaws.com/glikson-public/DLL/model/model_197x197.hdf5 -O /tmp/model.hdf5
ENV MODEL "https://s3.amazonaws.com/glikson-public/DLL/model/model_197x197.hdf5"
EXPOSE 80

CMD python manage.py runserver 0.0.0.0:80
