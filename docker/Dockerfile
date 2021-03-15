FROM robocomp/robocomp:focal
ARG branch=SplitComponent
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
    python3-geopandas \
    python3-opencv \
    python3-opengl \
    python3-pandas \
    python3-pygame \
    python3-yaml \
    python3-zeroc-ice \
    && sudo rm -rf /var/lib/apt/lists/*
RUN sudo pip3 install pyqtgraph
# get melex-rodao repository
USER robolab
RUN mkdir -p robocomp/components
WORKDIR robocomp/components
# With this ADD the image is regenerated for every change on git
ADD https://api.github.com/repos/robocomp/melex-rodao/git/refs/heads/SplitComponent version.json
RUN git clone -b $branch https://github.com/robocomp/melex-rodao.git
RUN cd melex-rodao && mkdir build && cd build && cmake .. && make && sudo PATH=$PATH make install
COPY --from=carlasim/carla:0.9.11 /home/carla/PythonAPI /home/robolab/CARLA_0.9.11/PythonAPI
RUN ln -s /home/robolab/CARLA_0.9.11/PythonAPI/carla/dist/carla-0.9.11-py3.7-linux-x86_64.egg /home/robolab/CARLA_0.9.11/PythonAPI/carla/dist/carla-0.9.11-py3.8-linux-x86_64.egg
WORKDIR melex-rodao/components/
RUN python3 carlaBridge/test/runtest.py



