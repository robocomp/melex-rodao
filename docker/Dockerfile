FROM robocomp/robocomp:focal_dev

# LABEL about the custom image
LABEL maintainer="emartinena@unex.es"
LABEL version="0.1"
LABEL description="This is custom Docker Image for Robocomp in Ubuntu Focal"

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

# Update Ubuntu Software repository
RUN sudo apt update && sudo apt install -y libopencv-dev python3-opencv python3-yaml python3-pygame
# get melex-rodao repository
WORKDIR components
RUN git clone https://github.com/robocomp/melex-rodao.git
RUN cd melex-rodao && git fetch && git checkout SplitComponent && git pull
RUN cd melex-rodao && mkdir build && cd build && cmake .. && make && sudo make install
WORKDIR melex-rodao/components/

# compile


