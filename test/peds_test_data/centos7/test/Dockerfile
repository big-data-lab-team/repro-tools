FROM centos:7

RUN curl https://bootstrap.pypa.io/get-pip.py | python

RUN yum update -y && yum install -y \
    which \
    git \
    gcc \
    gcc-c++ \
    python-argparse \
    python-devel \
    freetype-devel \
    libpng-devel

RUN pip install --upgrade pip && pip install \
    numpy \
    setuptools \
    matplotlib==1.4.3 \
    pandas \ 
    graphviz \ 
    boutiques \
    docker

RUN export PYTHONPATH="$PYTHONPATH:$PWD"

ADD test_script.sh /bin
