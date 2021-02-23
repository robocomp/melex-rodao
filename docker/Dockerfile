FROM robocomp/robocomp:focal

# LABEL about the custom image
LABEL maintainer="emartinena@unex.es"
LABEL version="0.1"
LABEL description="This is custom Docker Image for Robocomp in Ubuntu Focal"

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

# Update Ubuntu Software repository
RUN sudo apt update && sudo apt install -y libopencv-dev python3-opencv python3-yaml python3-pygame iputils-ping netcat git cmake make g++ gcc glmark2 python3-zeroc-ice
# get melex-rodao repository
USER robolab
RUN sudo ln -s ~ /home/robocomp
RUN mkdir components
WORKDIR components
RUN git clone https://github.com/robocomp/melex-rodao.git
RUN cd melex-rodao && git fetch && git checkout SplitComponent && git pull
ENV PATH $PATH:/opt/robocomp/bin/
RUN cd melex-rodao && mkdir build && cd build && cmake .. && make && sudo PATH=$PATH make install
COPY --from=carlasim/carla:0.9.11 /home/carla/PythonAPI /home/robolab/CARLA_0.9.11/PythonAPI
RUN ln -s /home/robolab/CARLA_0.9.11/PythonAPI/carla/dist/carla-0.9.11-py3.7-linux-x86_64.egg /home/robolab/CARLA_0.9.11/PythonAPI/carla/dist/carla-0.9.11-py3.8-linux-x86_64.egg
WORKDIR melex-rodao/components/

# compile


