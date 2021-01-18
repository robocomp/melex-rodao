# melex-rodao

In this project we use the simulator [CARLA](https://carla.readthedocs.io/en/latest/start_quickstart).
The easiest way to install them is following the steps indicated in point B from the [precompiled package](https://carla.readthedocs.io/en/latest/start_quickstart/#b-package-installation).

We are currently using CARLA [Development version 0.9.10](https://github.com/carla-simulator/carla/blob/master/Docs/download.md). You can download the [tar.gz file](https://carla-releases.s3.eu-west-3.amazonaws.com/Linux/CARLA_0.9.10.tar.gz) uncompres in your own carla directory, execute the ./ImportAssets.sh script and the installation is done.
```bash
wget https://carla-releases.s3.eu-west-3.amazonaws.com/Linux/CARLA_0.9.10.tar.gz
mkdir -p carla
tar -xvf CARLA_0.9.10.tar.gz -C carla 
cd carla
sh ImportAssets.sh
```


 


<!--stackedit_data:
eyJoaXN0b3J5IjpbLTMyMDcwMjU2OCwxNDM0ODkzMzEsMTY3OD
cyOTU4MywzNTgyMzY3ODZdfQ==
-->