cmake_minimum_required(VERSION 3.3)
project(hilbert
        VERSION 0.0
        LANGUAGES CXX)

add_library(hilbert src/hilbert.cpp)

target_include_directories(hilbert
        PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
        $<INSTALL_INTERFACE:include>
        )

install(TARGETS hilbert EXPORT hilbertConfig
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include)

# Importable from install
install(EXPORT hilbertConfig DESTINATION share/hilbert/cmake)
export(TARGETS hilbert FILE hilbertConfig.cmake)
