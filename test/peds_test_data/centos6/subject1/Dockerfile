FROM centos:centos6.8

RUN yum update -y && yum install -y https://centos6.iuscommunity.org/ius-release.rpm
RUN yum install -y  python36u-devel
RUN yum install -y python36u-pip



RUN yum update -y && yum install -y \
    which \
    git \
    gcc \
    gcc-c++ \
    python-argparse \
    python-devel \
    freetype-devel \
    libpng-devel

RUN pip3.6 install \
    numpy \
    setuptools \
    matplotlib==1.4.3 \
    pandas \
    graphviz \
    boutiques \
    docker

RUN echo 'alias python="/usr/bin/python3.6"' >> ~/.bashrc
RUN . ~/.bashrc

RUN rm /usr/bin/python
RUN ln -s /usr/bin/python3.6 /usr/bin/python

RUN export PYTHONPATH="$PYTHONPATH:$PWD"

ADD  test_script.sh /bin
