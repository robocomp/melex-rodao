cmake_minimum_required(VERSION 3.10)

INCLUDE( /opt/robocomp/cmake/robocomp.cmake )

ROBOCOMP_IDSL_TO_ICE( CommonBehavior CameraRGBDSimple CarCameraRGBD CarlaSensors CarlaVehicleControl MelexLogger )
