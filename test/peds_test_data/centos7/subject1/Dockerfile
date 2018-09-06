FROM centos:7

RUN curl https://bootstrap.pypa.io/get-pip.py | python

RUN yum update -y && yum install -y \
    which \
    git \
    gcc \
    wget \
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

RUN wget http://apache.mirror.gtcomm.net/spark/spark-2.3.1/spark-2.3.1-bin-hadoop2.7.tgz
RUN tar -xzf spark-2.3.1-bin-hadoop2.7.tgz
RUN export SPARK_HOME=`pwd`/spark-2.3.1-bin-hadoop2.7
RUN export PYTHONPATH=$SPARK_HOME/python:$PYTHONPATH
RUN export PYTHONPATH=$SPARK_HOME/python/lib/py4j-0.10.7-src.zip:$PYTHONPATH
RUN pip install pyspark

RUN export PYTHONPATH="$PYTHONPATH:$PWD"

ADD test_script.sh /bin