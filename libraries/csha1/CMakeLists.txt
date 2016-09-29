cmake_minimum_required(VERSION 3.3)
project(csha1
        VERSION 2.1
        LANGUAGES CXX)

add_library(csha1 src/SHA1.cpp)

target_include_directories(csha1
        PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
        )

install(TARGETS csha1 EXPORT csha1Config
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)

# Importable from install
install(EXPORT csha1Config DESTINATION share/csha1/cmake)
export(TARGETS csha1 FILE csha1Config.cmake)
