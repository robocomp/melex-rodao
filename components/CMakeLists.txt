cmake_minimum_required(VERSION 3.10)
project ( melex_rodao_components
		VERSION 2021.2.1
		DESCRIPTION "RoboComp melex-rodao components"
        LANGUAGES CXX
		)


IF ( "$ENV{ROBOCOMP}" STREQUAL "")
    MESSAGE(WARNING "ROBOCOMP variable not set. Using the default value: /opt/robocomp")
    SET (ENV{ROBOCOMP} "/opt/robocomp/")
ENDIF ( "$ENV{ROBOCOMP}" STREQUAL "")

IF(NOT EXISTS $ENV{ROBOCOMP}/cmake)
    MESSAGE(FATAL_ERROR "Couldn't find RoboComp in $ENV{ROBOCOMP}! Exiting...")
ENDIF(NOT EXISTS $ENV{ROBOCOMP}/cmake)

# INCLUDE( $ENV{ROBOCOMP}/cmake/robocomp.cmake )
# INCLUDE( $ENV{ROBOCOMP}/cmake/modules/qt.cmake )
# 

add_subdirectory(carlaBridge)
add_subdirectory(carlaMonitor)
