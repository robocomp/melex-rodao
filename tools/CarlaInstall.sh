wget https://carla-releases.s3.eu-west-3.amazonaws.com/Linux/CARLA_0.9.10.tar.gz
mkdir -p carla
tar -xvf CARLA_0.9.10.tar.gz -C carla 
cd carla
sh ImportAssets.sh
