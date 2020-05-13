FROM python:3.8-slim-buster

ADD lightspot /tmp/spot
RUN pip3 install --no-cache-dir /tmp/spot/
ADD  test_script.sh /bin
