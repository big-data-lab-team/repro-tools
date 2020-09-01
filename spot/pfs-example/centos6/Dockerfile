FROM bigdatalabteam/hcp-prefreesurfer:exec-centos6-fslbuild-centos5-latest

# Install ReproZip
RUN yum install -y \
    which \
    gcc \
    python \
    python-devel \
    sqlite-devel \
    gcc-c++ \
    python-argparse \
    freetype-devel \
    libpng-devel \
    python-pip \
    epel-release

RUN curl 'https://setup.ius.io/' -o setup-ius.sh &&\
    sh setup-ius.sh
RUN yum --enablerepo=ius install -y \
    python36u \
    python36u-devel \
    python36u-pip

RUN pip3.6 install -U reprozip

# Install spot tool
RUN cd /tmp/ && \
    git clone https://github.com/ali4006/spot.git &&\
    python3.6 -m pip install --no-cache-dir spot/lightspot/ &&\
    ln -s /usr/bin/python3.6 /usr/bin/python3
#    rm /usr/bin/python &&\
#    ln -s /usr/bin/python3.6 /usr/bin/python
RUN chown 1000:1000 /tmp

# Terminate pipeline after ACPC-A
# Add the following lines in ${HCPPIPEDIR}/PreFreeSurfer/PreFreeSurferPipeline.sh:
# 502     # Terminate our shell script with success message
# 503     log_Msg "ACPC-Alighnment is Done! We terminate the pipeline!"
# 504     exit 0

ADD spot/pfs-example/PreFreeSurferPipeline.sh \
    ${HOME}/pipelines/PreFreeSurfer/PreFreeSurferPipeline.sh
ADD spot/pfs-example/command-line-script.sh \
    /bin/command-line-script.sh
