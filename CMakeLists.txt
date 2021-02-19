cmake_minimum_required( VERSION 3.10)
project ( melex_rodaor
		VERSION 2021.2.1
		DESCRIPTION "RoboComp melex-rodao"
        LANGUAGES CXX
		)
		
add_subdirectory(components)		
install(DIRECTORY interfaces/IDSLs/
            DESTINATION /opt/robocomp/interfaces/IDSLs/
            FILES_MATCHING PATTERN "*.idsl"
            )
