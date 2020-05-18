FROM python:3.8-slim-buster

ADD lightspot /tmp/spot
RUN pip3 install --no-cache-dir /tmp/spot/
ADD spot/example/test_script.sh /bin
