# As of 2016-10, cmake version 3.3 is the latest included in conda.
cmake_minimum_required(VERSION 3.3)
project(OpenMM
        VERSION 7.0.0
        LANGUAGES CXX)

cmake_policy(SET CMP0003 NEW)
cmake_policy(SET CMP0005 NEW)
cmake_policy(SET CMP0011 NEW)
cmake_policy(SET CMP0042 OLD)

find_package(PythonInterp)
mark_as_advanced(CLEAR PYTHON_EXECUTABLE)

set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake_modules")

# Where to install
IF(WIN32)
    IF(NOT OPENMM_INSTALL_PREFIX)
        SET(OPENMM_INSTALL_PREFIX "$ENV{ProgramFiles}/OpenMM")
    ENDIF(NOT OPENMM_INSTALL_PREFIX)
ELSE(WIN32)
    IF(NOT OPENMM_INSTALL_PREFIX)
        SET(OPENMM_INSTALL_PREFIX "/usr/local/openmm")
    ENDIF(NOT OPENMM_INSTALL_PREFIX)
ENDIF(WIN32)

# Include CPU-Features for Android
IF (ANDROID)
    INCLUDE_DIRECTORIES(${ANDROID_NDK}/sources/cpufeatures)
ENDIF (ANDROID)

IF(${CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT})
  SET(CMAKE_INSTALL_PREFIX ${OPENMM_INSTALL_PREFIX} CACHE PATH "Where to install OpenMM" FORCE)
ENDIF(${CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT})



IF(APPLE AND (NOT PNACL))
    # Build 64 bit binaries compatible with OS X 10.7
    if(NOT CMAKE_OSX_DEPLOYMENT_TARGET)
        set(CMAKE_OSX_DEPLOYMENT_TARGET "10.7" CACHE STRING "The minimum version of OS X to support" FORCE)
    endif()
    if(NOT CMAKE_OSX_ARCHITECTURES)
        set(CMAKE_OSX_ARCHITECTURES "x86_64" CACHE STRING "The processor architectures to build for" FORCE)
    endif()
    if(NOT CMAKE_OSX_SYSROOT)
        execute_process(COMMAND "xcrun" "--show-sdk-path"
                        OUTPUT_VARIABLE XCRUN_OSX_SYSROOT
                        RESULT_VARIABLE XCRUN_OSX_SYSROOT_STATUS
                        OUTPUT_STRIP_TRAILING_WHITESPACE)
        if(XCRUN_OSX_SYSROOT_STATUS EQUAL 0)
            set(CMAKE_OSX_SYSROOT "${XCRUN_OSX_SYSROOT}" CACHE STRING "SDK Path" FORCE)
        endif()
        unset(XCRUN_OSX_SYSROOT)
        unset(XCRUN_OSX_SYSROOT_STATUS)
    endif(NOT CMAKE_OSX_SYSROOT)

    # Improve the linking behavior of Mac libraries
    set(CMAKE_INSTALL_NAME_DIR "@rpath")
    set(EXTRA_COMPILE_FLAGS "-msse2 -stdlib=libc++")
else(APPLE AND (NOT PNACL))
    if(MSVC OR ANDROID OR PNACL)
        set(EXTRA_COMPILE_FLAGS)
        if(MSVC)
            # Use warning level 2, not whatever warning level CMake picked.
            string(REGEX REPLACE "/W[0-4]" "/W2" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
            # Explicitly suppress warnings 4305 and 4244.
            set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /wd4305 /wd4244")
        endif(MSVC)
    else(MSVC OR ANDROID OR PNACL)
        set(EXTRA_COMPILE_FLAGS "-msse2")
    endif(MSVC OR ANDROID OR PNACL)
endif(APPLE AND (NOT PNACL))

if(UNIX AND NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Debug or Release build" FORCE)
endif(UNIX AND NOT CMAKE_BUILD_TYPE)

if(NOT CMAKE_CXX_FLAGS_DEBUG)
    set(CMAKE_CXX_FLAGS_DEBUG "-g" CACHE STRING "To use when CMAKE_BUILD_TYPE=Debug" FORCE)
endif(NOT CMAKE_CXX_FLAGS_DEBUG)

if(NOT CMAKE_CXX_FLAGS_RELEASE)
    if(ANDROID)
        set(CMAKE_CXX_FLAGS_RELEASE "-mfloat-abi=softfp -march=armv7-a -mfpu=neon -funsafe-math-optimizations -O3 -DNDEBUG"
            CACHE STRING "To use when CMAKE_BUILD_TYPE=Release" FORCE)
    else(ANDROID)
        set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG"
            CACHE STRING "To use when CMAKE_BUILD_TYPE=Release" FORCE)
    endif(ANDROID)
endif(NOT CMAKE_CXX_FLAGS_RELEASE)


# Collect up information about the version of the OpenMM library we're building
# and make it available to the code so it can be built into the binaries.

SET(OPENMM_LIBRARY_NAME OpenMM)

SET(OPENMM_COPYRIGHT_YEARS "2008-2015")

# underbar separated list of dotted authors, no spaces or commas
SET(OPENMM_AUTHORS "Peter.Eastman")

# TODO: Change this to configure_file.
ADD_DEFINITIONS(-DOPENMM_LIBRARY_NAME=${OPENMM_LIBRARY_NAME}
                -DOPENMM_MAJOR_VERSION=${OpenMM_VERSION_MAJOR}
                -DOPENMM_MINOR_VERSION=${OpenMM_VERSION_MINOR}
                -DOPENMM_BUILD_VERSION=${OpenMM_VERSION_PATCH})


ADD_DEFINITIONS(-DOPENMM_COPYRIGHT_YEARS="${OPENMM_COPYRIGHT_YEARS}"
                -DOPENMM_AUTHORS="${OPENMM_AUTHORS}")


SET(SHARED_TARGET ${OPENMM_LIBRARY_NAME})
SET(STATIC_TARGET ${OPENMM_LIBRARY_NAME}_static)

# used by plugin
SET(OPENMM_DIR ${CMAKE_CURRENT_SOURCE_DIR})


# The source is organized into subdirectories, but we handle them all from
# this CMakeLists file rather than letting CMake visit them as SUBDIRS.
SET(OPENMM_SOURCE_SUBDIRS
        .
        openmmapi
        olla
        serialization
        platforms/reference
        libraries/jama
        libraries/quern
        libraries/lepton
        libraries/sfmt
        libraries/lbfgs
        libraries/vecmath)
IF(WIN32)
    SET(OPENMM_SOURCE_SUBDIRS ${OPENMM_SOURCE_SUBDIRS} libraries/pthreads)
ELSE(WIN32)
    IF (NOT ANDROID)
        SET(PTHREADS_LIB pthread)
        # in linux, even in static builds we link against the dynamic object (since its tied to libc versions)
        SET(PTHREADS_LIB_STATIC pthread)
    ENDIF (NOT ANDROID)
ENDIF(WIN32)

if(NOT (ANDROID OR PNACL))
    add_subdirectory(libraries/asmjit)
    set(EXTRA_COMPILE_FLAGS "${EXTRA_COMPILE_FLAGS} -DLEPTON_USE_JIT") #TODO: better way of doing this?
endif()
add_subdirectory(libraries/csha1)
add_subdirectory(libraries/hilbert)
add_subdirectory(libraries/irrxml)

# collect up source files
SET(SOURCE_FILES) # empty
SET(SOURCE_INCLUDE_FILES)

FOREACH(subdir ${OPENMM_SOURCE_SUBDIRS})
    FILE(GLOB src_files  ${CMAKE_CURRENT_SOURCE_DIR}/${subdir}/src/*.cpp ${CMAKE_CURRENT_SOURCE_DIR}/${subdir}/src/*/*.cpp)
    FILE(GLOB incl_files ${CMAKE_CURRENT_SOURCE_DIR}/${subdir}/src/*.h)
    SET(SOURCE_FILES         ${SOURCE_FILES}         ${src_files})   #append
    SET(SOURCE_INCLUDE_FILES ${SOURCE_INCLUDE_FILES} ${incl_files})

    ## Make sure we find these locally before looking in OpenMM/include if
    ## OpenMM was previously installed there.
    INCLUDE_DIRECTORIES(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}/${subdir}/include)
ENDFOREACH(subdir)

IF (ANDROID OR PNACL)
    SET_SOURCE_FILES_PROPERTIES(${CMAKE_SOURCE_DIR}/libraries/sfmt/src/SFMT.cpp PROPERTIES COMPILE_FLAGS "-UHAVE_SSE2")
ELSE (ANDROID OR PNACL)
    SET_SOURCE_FILES_PROPERTIES(${CMAKE_SOURCE_DIR}/libraries/sfmt/src/SFMT.cpp PROPERTIES COMPILE_FLAGS "-DHAVE_SSE2=1")
ENDIF(ANDROID OR PNACL)

# If API wrappers are being generated, and add them to the build.
SET(OPENMM_BUILD_C_AND_FORTRAN_WRAPPERS ON CACHE BOOL "Build wrappers for C and Fortran")
IF(OPENMM_BUILD_C_AND_FORTRAN_WRAPPERS)
    ADD_SUBDIRECTORY(wrappers)
    SET(SOURCE_FILES ${SOURCE_FILES} wrappers/OpenMMCWrapper.cpp  wrappers/OpenMMFortranWrapper.cpp)
    SET_SOURCE_FILES_PROPERTIES(wrappers/OpenMMCWrapper.cpp wrappers/OpenMMFortranWrapper.cpp PROPERTIES GENERATED TRUE)
ENDIF(OPENMM_BUILD_C_AND_FORTRAN_WRAPPERS)

INCLUDE_DIRECTORIES(BEFORE ${CMAKE_CURRENT_SOURCE_DIR}/src)

SET(OPENMM_BUILD_SHARED_LIB ON CACHE BOOL "Whether to build shared OpenMM libraries")

SET(EXTRA_LINK_FLAGS ${EXTRA_COMPILE_FLAGS})
IF (CMAKE_SYSTEM_NAME MATCHES "Linux")
    IF (NOT ANDROID)
        SET(EXTRA_LINK_FLAGS "${EXTRA_LINK_FLAGS} -Wl,--no-as-needed -lrt")
    ENDIF (NOT ANDROID)
ENDIF (CMAKE_SYSTEM_NAME MATCHES "Linux")
IF (MSVC)
    SET(EXTRA_LINK_FLAGS)
ENDIF (MSVC)

IF(OPENMM_BUILD_SHARED_LIB)
    ADD_LIBRARY(${SHARED_TARGET} SHARED ${SOURCE_FILES} ${SOURCE_INCLUDE_FILES} ${API_ABS_INCLUDE_FILES})
    SET_TARGET_PROPERTIES(${SHARED_TARGET} PROPERTIES LINK_FLAGS "${EXTRA_LINK_FLAGS}" COMPILE_FLAGS "${EXTRA_COMPILE_FLAGS} -DOPENMM_BUILDING_SHARED_LIBRARY -DLEPTON_BUILDING_SHARED_LIBRARY -DPTHREAD_BUILDING_SHARED_LIBRARY")
ENDIF(OPENMM_BUILD_SHARED_LIB)

SET(OPENMM_BUILD_STATIC_LIB OFF CACHE BOOL "Whether to build static OpenMM libraries")
IF(OPENMM_BUILD_STATIC_LIB)
    ADD_LIBRARY(${STATIC_TARGET} STATIC ${SOURCE_FILES} ${SOURCE_INCLUDE_FILES} ${API_ABS_INCLUDE_FILES})
    SET(EXTRA_COMPILE_FLAGS "${EXTRA_COMPILE_FLAGS} -DOPENMM_USE_STATIC_LIBRARIES -DLEPTON_USE_STATIC_LIBRARIES -DPTW32_STATIC_LIB")
    SET_TARGET_PROPERTIES(${STATIC_TARGET} PROPERTIES LINK_FLAGS "${EXTRA_LINK_FLAGS}" COMPILE_FLAGS "${EXTRA_COMPILE_FLAGS} -DOPENMM_BUILDING_STATIC_LIBRARY -DLEPTON_BUILDING_STATIC_LIBRARY -DPTHREAD_BUILDING_STATIC_LIBRARY")
ENDIF(OPENMM_BUILD_STATIC_LIB)

IF(OPENMM_BUILD_C_AND_FORTRAN_WRAPPERS)
    ADD_DEPENDENCIES(${SHARED_TARGET} ApiWrappers)
    IF(OPENMM_BUILD_STATIC_LIB)
        ADD_DEPENDENCIES(${STATIC_TARGET} ApiWrappers)
    ENDIF(OPENMM_BUILD_STATIC_LIB)
ENDIF(OPENMM_BUILD_C_AND_FORTRAN_WRAPPERS)

# On Linux need to link to libdl
FIND_LIBRARY(DL_LIBRARY dl)
IF(DL_LIBRARY)
    IF(OPENMM_BUILD_SHARED_LIB)
        TARGET_LINK_LIBRARIES(${SHARED_TARGET} ${DL_LIBRARY} ${PTHREADS_LIB})
    ENDIF(OPENMM_BUILD_SHARED_LIB)
    IF(OPENMM_BUILD_STATIC_LIB)
        TARGET_LINK_LIBRARIES(${STATIC_TARGET} ${DL_LIBRARY} ${PTHREADS_LIB})
    ENDIF(OPENMM_BUILD_STATIC_LIB)
    MARK_AS_ADVANCED(DL_LIBRARY)
ELSE(DL_LIBRARY)
    IF(OPENMM_BUILD_SHARED_LIB)
        IF (ANDROID)
            TARGET_LINK_LIBRARIES(${SHARED_TARGET} ${PTHREADS_LIB} cpufeatures)
        ELSE (ANDROID)
            TARGET_LINK_LIBRARIES(${SHARED_TARGET} ${PTHREADS_LIB})
        ENDIF (ANDROID)
    ENDIF(OPENMM_BUILD_SHARED_LIB)
ENDIF(DL_LIBRARY)

IF(BUILD_TESTING)
    INCLUDE_DIRECTORIES(${CMAKE_SOURCE_DIR}/tests)
ENDIF(BUILD_TESTING)

set(OPENMM_BUILD_REFERENCE_TESTS TRUE CACHE BOOL "Whether to build Reference platform test cases")
MARK_AS_ADVANCED(OPENMM_BUILD_REFERENCE_TESTS)
IF(BUILD_TESTING AND OPENMM_BUILD_REFERENCE_TESTS)
    ADD_SUBDIRECTORY(platforms/reference/tests)
ENDIF(BUILD_TESTING AND OPENMM_BUILD_REFERENCE_TESTS)

# Which hardware platforms to build

# A bit of tedium because we are using custom FindCUDA files that happen to work...
SET(FINDCUDA_DIR "${CMAKE_CURRENT_SOURCE_DIR}/cmake_modules/FindCUDA")
SET(CUDA_BUILD_CUBIN OFF)
FIND_PACKAGE(CUDA QUIET)
IF(CUDA_FOUND)
    IF(NOT CUDA_NVCC_FLAGS)
        SET(FLAGS "")
        # Note that cmake will insert semicolons between these item automatically...
        SET(FLAGS ${FLAGS} -gencode arch=compute_11,code=sm_11)
        SET(FLAGS ${FLAGS} -gencode arch=compute_12,code=sm_12)
        SET(FLAGS ${FLAGS} -gencode arch=compute_13,code=sm_13)
        SET(FLAGS ${FLAGS} -gencode arch=compute_20,code=sm_20)
        SET(FLAGS ${FLAGS} -use_fast_math)
        IF(MSVC)
            # Unfortunately the variables CUDA_NVCC_FLAGS_RELEASE and CUDA_NVCC_FLAGS_DEBUG
            # appear to be unused, at least in CMake 2.6
            # Release /MD linkage
            set(FLAGS ${FLAGS} "-Xcompiler \"/MD\" -DOPENMMCUDA_BUILDING_SHARED_LIBRARY")
        ENDIF(MSVC)
        SET(CUDA_NVCC_FLAGS  "${FLAGS}"
            CACHE STRING "Semicolon delimit multiple arguments")
    ENDIF(NOT CUDA_NVCC_FLAGS)
    SET(OPENMM_BUILD_CUDA_LIB ON CACHE BOOL "Build OpenMMCuda library for Nvidia GPUs")

    # I wish I was not hardcoding /MD here
    # Avoid strange windows link error with cuda free energy
    # plugin by specifying /MD to CUDA_NVCC_FLAGS
    MARK_AS_ADVANCED(CLEAR CUDA_NVCC_FLAGS)
    IF(MSVC)
        # Unfortunately the variables CUDA_NVCC_FLAGS_RELEASE and CUDA_NVCC_FLAGS_DEBUG
        # appear to be unused, at least in CMake 2.6
        # Release /MD linkage
        SET(HAS_NVCC_FLAG FALSE)
        IF(CUDA_NVCC_FLAGS MATCHES "-Xcompiler")
            SET(HAS_NVCC_FLAG TRUE)
        ENDIF(CUDA_NVCC_FLAGS MATCHES "-Xcompiler")
        IF(NOT HAS_NVCC_FLAG)
            set(new_flags "-Xcompiler \"/MD\" -DOPENMMCUDA_BUILDING_SHARED_LIBRARY")
            if(CUDA_NVCC_FLAGS)
                set(new_flags "${CUDA_NVCC_FLAGS};${new_flags}")
            endif(CUDA_NVCC_FLAGS)
            SET(CUDA_NVCC_FLAGS "${new_flags}"
                CACHE STRING "Semicolon delimit multiple arguments" FORCE)
        ENDIF(NOT HAS_NVCC_FLAG)
    ENDIF(MSVC)
ELSE(CUDA_FOUND)
    SET(OPENMM_BUILD_CUDA_LIB OFF CACHE BOOL "Build OpenMMCuda library for Nvidia GPUs")
ENDIF(CUDA_FOUND)
IF(OPENMM_BUILD_CUDA_LIB)
    ADD_SUBDIRECTORY(platforms/cuda)
ENDIF(OPENMM_BUILD_CUDA_LIB)
MARK_AS_ADVANCED(CUDA_VERBOSE_BUILD)
MARK_AS_ADVANCED(CUDA_BUILD_CUBIN)
MARK_AS_ADVANCED(CUDA_BUILD_EMULATION)
MARK_AS_ADVANCED(CUDA_HOST_COMPILER CUDA_HOST_COMPILER_OPTIONS)

FIND_PACKAGE(OpenCL QUIET)
IF(OPENCL_FOUND)
    SET(OPENMM_BUILD_OPENCL_LIB ON CACHE BOOL "Build OpenMMOpenCL library")
ELSE(OPENCL_FOUND)
    SET(OPENMM_BUILD_OPENCL_LIB OFF CACHE BOOL "Build OpenMMOpenCL library")
ENDIF(OPENCL_FOUND)
IF(OPENMM_BUILD_OPENCL_LIB)
    ADD_SUBDIRECTORY(platforms/opencl)
ENDIF(OPENMM_BUILD_OPENCL_LIB)

# Optimized CPU platform

SET(OPENMM_BUILD_CPU_LIB ON CACHE BOOL "Build optimized CPU platform")
IF(OPENMM_BUILD_CPU_LIB)
   ADD_SUBDIRECTORY(platforms/cpu)
ENDIF(OPENMM_BUILD_CPU_LIB)

# Amoeba plugin

SET(OPENMM_BUILD_AMOEBA_PLUGIN ON CACHE BOOL "Build Amoeba plugin")
SET(OPENMM_BUILD_AMOEBA_PATH)
IF(OPENMM_BUILD_AMOEBA_PLUGIN)
   SET(OPENMM_BUILD_AMOEBA_PATH ${CMAKE_CURRENT_SOURCE_DIR}/plugins/amoeba)
   ADD_SUBDIRECTORY(plugins/amoeba)
ENDIF(OPENMM_BUILD_AMOEBA_PLUGIN)

# RPMD plugin

SET(OPENMM_BUILD_RPMD_PLUGIN ON CACHE BOOL "Build RPMD plugin")
SET(OPENMM_BUILD_RPMD_PATH)
IF(OPENMM_BUILD_RPMD_PLUGIN)
   SET(OPENMM_BUILD_RPMD_PATH ${CMAKE_CURRENT_SOURCE_DIR}/plugins/rpmd)
   ADD_SUBDIRECTORY(plugins/rpmd)
ENDIF(OPENMM_BUILD_RPMD_PLUGIN)

# Drude plugin

SET(OPENMM_BUILD_DRUDE_PLUGIN ON CACHE BOOL "Build Drude plugin")
SET(OPENMM_BUILD_DRUDE_PATH)
IF(OPENMM_BUILD_DRUDE_PLUGIN)
   SET(OPENMM_BUILD_DRUDE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/plugins/drude)
   ADD_SUBDIRECTORY(plugins/drude)
ENDIF(OPENMM_BUILD_DRUDE_PLUGIN)

# CPU PME plugin

FIND_PACKAGE(FFTW QUIET)
IF(FFTW_FOUND)
    SET(OPENMM_BUILD_PME_PLUGIN ON CACHE BOOL "Build CPU PME plugin")
ELSE(FFTW_FOUND)
    SET(OPENMM_BUILD_PME_PLUGIN OFF CACHE BOOL "Build CPU PME plugin")
ENDIF(FFTW_FOUND)
SET(OPENMM_BUILD_PME_PATH)
IF(OPENMM_BUILD_PME_PLUGIN)
   SET(OPENMM_BUILD_PME_PATH ${CMAKE_CURRENT_SOURCE_DIR}/plugins/cpupme)
   ADD_SUBDIRECTORY(plugins/cpupme)
ENDIF(OPENMM_BUILD_PME_PLUGIN)

# CUDA compiler plugin

GET_FILENAME_COMPONENT(CUDA_LIB_DIR "${CUDA_cufft_LIBRARY}" PATH)
FIND_LIBRARY(CUDA_nvrtc_LIBRARY nvrtc "${CUDA_LIB_DIR}")
IF(CUDA_nvrtc_LIBRARY)
    SET(OPENMM_BUILD_CUDA_COMPILER_PLUGIN ON CACHE BOOL "Build CUDA runtime compiler plugin")
ELSE(CUDA_nvrtc_LIBRARY)
    SET(OPENMM_BUILD_CUDA_COMPILER_PLUGIN OFF CACHE BOOL "Build CUDA runtime compiler plugin")
ENDIF(CUDA_nvrtc_LIBRARY)
SET(OPENMM_BUILD_CUDACOMPILER_PATH)
IF(OPENMM_BUILD_CUDA_COMPILER_PLUGIN)
   SET(OPENMM_BUILD_CUDACOMPILER_PATH ${CMAKE_CURRENT_SOURCE_DIR}/plugins/cudacompiler)
   ADD_SUBDIRECTORY(plugins/cudacompiler)
ENDIF(OPENMM_BUILD_CUDA_COMPILER_PLUGIN)

IF(OPENMM_BUILD_SHARED_LIB)
    INSTALL_TARGETS(/lib RUNTIME_DIRECTORY /lib ${SHARED_TARGET})
ENDIF(OPENMM_BUILD_SHARED_LIB)
IF(OPENMM_BUILD_STATIC_LIB)
  INSTALL_TARGETS(/lib RUNTIME_DIRECTORY /lib ${STATIC_TARGET})
ENDIF(OPENMM_BUILD_STATIC_LIB)
FILE(GLOB CORE_HEADERS     include/*.h          */include/*.h)
FILE(GLOB TOP_HEADERS      include/openmm/*.h          */include/openmm/*.h)
FILE(GLOB INTERNAL_HEADERS include/openmm/internal/*.h */include/openmm/internal/*.h )
FILE(GLOB REFERENCE_HEADERS platforms/reference/include/*.h)
FILE(GLOB LEPTON_HEADERS   libraries/lepton/include/lepton/*.h)
FILE(GLOB SFMT_HEADERS     libraries/sfmt/include/sfmt/SFMT.h)
INSTALL_FILES(/include                 FILES ${CORE_HEADERS})
INSTALL_FILES(/include/openmm          FILES ${TOP_HEADERS})
INSTALL_FILES(/include/openmm/internal FILES ${INTERNAL_HEADERS})
INSTALL_FILES(/include/openmm/reference FILES ${REFERENCE_HEADERS})
INSTALL_FILES(/include/lepton          FILES ${LEPTON_HEADERS})
INSTALL_FILES(/include/sfmt            FILES ${SFMT_HEADERS})

# Serialization support

ADD_SUBDIRECTORY(serialization)
FILE(GLOB serialization_files  ${CMAKE_SOURCE_DIR}/serialization/src/*.cpp)
SET_SOURCE_FILES_PROPERTIES(${serialization_files} PROPERTIES COMPILE_FLAGS "-DOPENMM_BUILDING_SHARED_LIBRARY -DTIXML_USE_STL -DIEEE_8087")

# Python wrappers

SET(OPENMM_BUILD_PYTHON_WRAPPERS ON CACHE BOOL "Build wrappers for Python")
IF(OPENMM_BUILD_PYTHON_WRAPPERS)
    IF(NOT OPENMM_BUILD_AMOEBA_PLUGIN)
        MESSAGE(SEND_ERROR "The Python wrappers require that the AMOEBA plugin be built.")
    ENDIF(NOT OPENMM_BUILD_AMOEBA_PLUGIN)
    IF(NOT OPENMM_BUILD_RPMD_PLUGIN)
        MESSAGE(SEND_ERROR "The Python wrappers require that the RPMD plugin be built.")
    ENDIF(NOT OPENMM_BUILD_RPMD_PLUGIN)
    IF(NOT OPENMM_BUILD_DRUDE_PLUGIN)
        MESSAGE(SEND_ERROR "The Python wrappers require that the Drude plugin be built.")
    ENDIF(NOT OPENMM_BUILD_DRUDE_PLUGIN)
    ADD_SUBDIRECTORY(wrappers/python)
ENDIF(OPENMM_BUILD_PYTHON_WRAPPERS)



#IF (UNIX AND NOT CYGWIN AND NOT APPLE)
#  IF (NOT CMAKE_BUILD_TYPE OR CMAKE_BUILD_TYPE MATCHES Debug)
#    ADD_DEFINITIONS(-fprofile-arcs -ftest-coverage)
#    LINK_LIBRARIES(gcov)
#  ENDIF (NOT CMAKE_BUILD_TYPE OR CMAKE_BUILD_TYPE MATCHES Debug)
#ENDIF (UNIX AND NOT CYGWIN AND NOT APPLE)


#
# Testing
#

ENABLE_TESTING()

IF (EXECUTABLE_OUTPUT_PATH)
  SET (TEST_PATH ${EXECUTABLE_OUTPUT_PATH})
ELSE (EXECUTABLE_OUTPUT_PATH)
  SET (TEST_PATH .)
ENDIF (EXECUTABLE_OUTPUT_PATH)

ADD_SUBDIRECTORY(docs-source)
IF(BUILD_TESTING)
    ADD_SUBDIRECTORY(tests)
ENDIF(BUILD_TESTING)

SET(OPENMM_BUILD_EXAMPLES ON CACHE BOOL "Build example executables")
IF(OPENMM_BUILD_EXAMPLES)
  ADD_SUBDIRECTORY(examples)
ENDIF(OPENMM_BUILD_EXAMPLES)

