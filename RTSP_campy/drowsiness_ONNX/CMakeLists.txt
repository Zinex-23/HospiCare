cmake_minimum_required(VERSION 3.14)
project(drowsiness_onnx_cpp LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(OpenCV REQUIRED)

set(ONNXRUNTIME_ROOT "" CACHE PATH "Path to ONNX Runtime SDK root (contains include/ and lib/)")
if(NOT ONNXRUNTIME_ROOT)
  set(ONNXRUNTIME_ROOT "${CMAKE_SOURCE_DIR}/third_party/onnxruntime")
endif()

find_path(ONNXRUNTIME_INCLUDE_DIR
  NAMES onnxruntime_cxx_api.h
  PATHS
    "${ONNXRUNTIME_ROOT}/include"
    "${ONNXRUNTIME_ROOT}/include/onnxruntime/core/session"
    "/usr/include/onnxruntime/core/session"
)

find_library(ONNXRUNTIME_LIB
  NAMES onnxruntime libonnxruntime libonnxruntime.so libonnxruntime.so.1.24.2
  PATHS
    "${ONNXRUNTIME_ROOT}/lib"
    "${ONNXRUNTIME_ROOT}/lib64"
    "/usr/lib"
    "/usr/lib/x86_64-linux-gnu"
)

if(NOT ONNXRUNTIME_LIB)
  find_file(ONNXRUNTIME_LIB
    NAMES libonnxruntime.so libonnxruntime.so.1.24.2
    PATHS
      "${ONNXRUNTIME_ROOT}/lib"
      "${ONNXRUNTIME_ROOT}/lib64"
      "/usr/lib"
      "/usr/lib/x86_64-linux-gnu"
  )
endif()

if(NOT ONNXRUNTIME_INCLUDE_DIR OR NOT ONNXRUNTIME_LIB)
  message(FATAL_ERROR "ONNX Runtime not found. Set -DONNXRUNTIME_ROOT=/path/to/onnxruntime")
endif()

add_executable(drowsiness_cam src/main.cpp)
target_include_directories(drowsiness_cam PRIVATE ${ONNXRUNTIME_INCLUDE_DIR})
target_link_libraries(drowsiness_cam PRIVATE ${OpenCV_LIBS} ${ONNXRUNTIME_LIB})
target_compile_options(drowsiness_cam PRIVATE -O2 -Wall -Wextra)

get_filename_component(ONNXRUNTIME_LIB_DIR ${ONNXRUNTIME_LIB} DIRECTORY)
set_target_properties(drowsiness_cam PROPERTIES
  BUILD_RPATH "${ONNXRUNTIME_LIB_DIR}"
  INSTALL_RPATH "${ONNXRUNTIME_LIB_DIR}"
)

message(STATUS "ONNXRUNTIME_INCLUDE_DIR=${ONNXRUNTIME_INCLUDE_DIR}")
message(STATUS "ONNXRUNTIME_LIB=${ONNXRUNTIME_LIB}")
