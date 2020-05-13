FROM centos:centos6.8

RUN yum update -y
RUN yum install -y gcc zlib-devel openssl-devel \
                   which git sqlite-devel wheel
# install python3
RUN mkdir /build && cd /build && \
	curl -O https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz && \
	tar xzf Python-3.5.2.tgz && cd Python-3.5.2 && \
	./configure && make && make install && \
	rm -rf /build

RUN pip3 install --upgrade pip
RUN pip3 install jsonschema pandas scipy sklearn pytest

RUN  cd /tmp/ && \
     git clone https://github.com/ali4006/spot.git

RUN  pip3 install /tmp/spot/

RUN rm /usr/bin/python
RUN ln -s /usr/local/bin/python3.5 /usr/bin/python

ADD test_script.sh /bin
