FROM bigdatalabteam/hcp-prefreesurfer:exec-centos7-reprozip.fslbuild-centos5

#RUN yum -y update; yum clean all 
RUN yum clean all &&\
    yum -y install epel-release which; yum clean all &&\
    yum -y install python3-pip; yum clean all

# Install lightspot tool    
RUN cd /tmp/ &&\
    git clone https://github.com/ali4006/spot.git; yum clean all &&\
    pip3 install --no-cache-dir spot/lightspot/
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

