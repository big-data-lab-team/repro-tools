FROM centos:centos7

RUN yum -y update; yum clean all &&\
    yum -y install epel-release which; yum clean all &&\
    yum -y install python3-pip; yum clean all

ADD lightspot /tmp/spot
RUN pip3 install --no-cache-dir /tmp/spot/ &&\
    rm /usr/bin/python &&\
    ln -s /usr/bin/python3.6 /usr/bin/python
ADD  spot/example/test_script.sh /bin
