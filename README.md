# melex-rodao

In this project we use the simulator [CARLA](https://carla.readthedocs.io/en/latest/start_quickstart).
The easiest way to install them is following the steps indicated in point B from the [precompiled package](https://carla.readthedocs.io/en/latest/start_quickstart/#b-package-installation).

We are currently using CARLA [Development version 0.9.10](https://github.com/carla-simulator/carla/blob/master/Docs/download.md). You can download the [tar.gz file](https://carla-releases.s3.eu-west-3.amazonaws.com/Linux/CARLA_0.9.10.tar.gz) uncompres in your own carla directory, execute the ./ImportAssets.sh script and the isstallation is done.
```bash
wget https://carla-releases.s3.eu-west-3.amazonaws.com/Linux/CARLA_0.9.10.tar.gz
mkdir -p carla
tar -xvf CARLA_0.9.10.tar.gz -C carla 
cd carla
sh ImportAssets.sh
```
Try to execute the PythonAPI example manual_control.py
You may need to install some packages to make it work. You can do it manually or just execute:
sudo pip3 install -r requirements.txt
in the examples directory.


```bash
ln -s PythonAPI/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg PythonAPI/carla/dist/carla-0.9.10-py3.8-linux-x86_64.egg
```

 


<!--stackedit_data:
eyJoaXN0b3J5IjpbMTY0MDk2ODQ2MCwtODI4OTkzODIwLDExMj
cxNTQ2NDUsMTQzNDg5MzMxLDE2Nzg3Mjk1ODMsMzU4MjM2Nzg2
XX0=
-->