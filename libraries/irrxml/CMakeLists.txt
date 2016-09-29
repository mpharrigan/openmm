cmake_minimum_required(VERSION 3.3)
project(irrxml
        VERSION 1.2
        LANGUAGES CXX)

add_library(irrxml src/irrXML.cpp)

target_include_directories(irrxml
        PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
        )

install(TARGETS irrxml EXPORT irrxmlConfig
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)

# Importable from install
install(EXPORT irrxmlConfig DESTINATION share/irrxml/cmake)
export(TARGETS irrxml FILE irrxmlConfig.cmake)
