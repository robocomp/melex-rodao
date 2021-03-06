FROM robocomp/robocomp:focal

# LABEL about the custom image
LABEL maintainer="emartinena@unex.es"
LABEL version="0.1"
LABEL description="This is custom Docker Image for Robocomp in Ubuntu Focal"

# Disable Prompt During Packages Installation
ARG DEBIAN_FRONTEND=noninteractive

# Update Ubuntu Software repository
RUN sudo apt update && sudo apt install -y \
    cmake \
    g++ \
    gcc \
    git \
    glmark2 \
    iputils-ping \
    libopencv-dev \
    make \
    netcat \
    python3-opencv \
    python3-pygame \
    python3-yaml \
    python3-zeroc-ice \
    && sudo rm -rf /var/lib/apt/lists/*
#RUN apt-get update && apt-get install -y --no-install-recommends pyside2-tools
RUN sudo apt update && sudo apt install -y vim
# get melex-rodao repository
USER robolab
RUN sudo ln -s ~ /home/robocomp
RUN mkdir -p robocomp/components
WORKDIR robocomp/components
ADD https://api.github.com/repos/robocomp/melex-rodao/git/refs/heads/SplitComponent version.json
RUN git clone -b SplitComponent https://github.com/robocomp/melex-rodao.git
ENV PATH $PATH:/opt/robocomp/bin/
RUN cd melex-rodao && mkdir build && cd build && cmake .. && make && sudo PATH=$PATH make install
COPY --from=carlasim/carla:0.9.11 /home/carla/PythonAPI /home/robolab/CARLA_0.9.11/PythonAPI
RUN ln -s /home/robolab/CARLA_0.9.11/PythonAPI/carla/dist/carla-0.9.11-py3.7-linux-x86_64.egg /home/robolab/CARLA_0.9.11/PythonAPI/carla/dist/carla-0.9.11-py3.8-linux-x86_64.egg
WORKDIR melex-rodao/components/

# compile


