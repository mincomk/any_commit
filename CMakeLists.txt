cmake_minimum_required(VERSION 3.10)
project(MyCUDAProject LANGUAGES CXX CUDA)

# add_compile_options("$<$<CXX_COMPILER_ID:MSVC>:/source-charset:utf-8 /execution-charset:utf-8>")
set(CMAKE_CXX_STANDARD 17)

set(SOURCES
    src/main.cu
)

add_executable(my_cuda_app ${SOURCES})

set_target_properties(my_cuda_app PROPERTIES
    CUDA_ARCHITECTURES 89
)
