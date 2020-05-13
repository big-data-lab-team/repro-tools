FROM centos:7

RUN  yum install -y \
     which \
     python \
     python-devel \
     gcc \
     sqlite-devel \
     openssl-devel \
     libffi-devel \
     git

RUN curl https://bootstrap.pypa.io/get-pip.py | python
RUN pip install -U reprozip

RUN  cd /tmp/ && \
     git clone https://github.com/ali4006/spot.git
RUN  pip install /tmp/spot/

ADD test_script.sh /bin
