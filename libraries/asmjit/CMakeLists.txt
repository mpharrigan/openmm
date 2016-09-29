cmake_minimum_required(VERSION 3.3)
project(asmjit
        VERSION 0.0
        LANGUAGES CXX)

set(asmjit_base_SOURCE_FILES
        base/assembler.cpp
        base/codegen.cpp
        base/compiler.cpp
        base/constpool.cpp
        base/containers.cpp
        base/context.cpp
        base/cpuinfo.cpp
        base/cputicks.cpp
        base/error.cpp
        base/globals.cpp
        base/intutil.cpp
        base/logger.cpp
        base/operand.cpp
        base/runtime.cpp
        base/string.cpp
        base/vmem.cpp
        base/zone.cpp
        )

set(asmjir_x86_SOURCE_FILES
        x86/x86assembler.cpp
        x86/x86compiler.cpp
        x86/x86context.cpp
        x86/x86inst.cpp
        x86/x86operand.cpp
        x86/x86operand_regs.cpp
        x86/x86scheduler.cpp
        )

add_library(asmjit ${asmjit_base_SOURCE_FILES} ${asmjit_x86_SOURCE_FILES})

target_include_directories(asmjit
        PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/>
        $<INSTALL_INTERFACE:include>
        PRIVATE
        base/ x86/
        )

install(TARGETS asmjit EXPORT asmjitConfig
        ARCHIVE DESTINATION lib
        LIBRARY DESTINATION lib
        RUNTIME DESTINATION bin)
install(DIRECTORY include/ DESTINATION include) #TODO

# Importable from install
install(EXPORT asmjitConfig DESTINATION share/asmjit/cmake)
export(TARGETS asmjit FILE asmjitConfig.cmake)
