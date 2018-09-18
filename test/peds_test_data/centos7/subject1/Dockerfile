FROM centos:7

RUN  yum install -y \
     which \
     python \
     python-devel \
     gcc \
     sqlite-devel \
     openssl-devel \
     libffi-devel

RUN curl https://bootstrap.pypa.io/get-pip.py | python
RUN pip install -U reprozip

ADD test_script.sh /bin
