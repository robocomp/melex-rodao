pip3 install numpy ice PySide2 argparse termcolor pygame
wget https://carla-releases.s3.eu-west-3.amazonaws.com/Linux/CARLA_0.9.11.tar.gz
mkdir -p ../files/carla
tar -xvf CARLA_0.9.11.tar.gz -C ../files/carla
cd ../files/carla
sh ImportAssets.sh
