cmake_minimum_required(VERSION 2.6)
PROJECT(  carlaBridge )

INCLUDE( /opt/robocomp/cmake/robocomp.cmake )

ROBOCOMP_IDSL_TO_ICE( CommonBehavior AdminBridge CameraRGBDSimple CameraRGBDSimplePub CarlaSensors CarlaVehicleControl MelexLogger )
