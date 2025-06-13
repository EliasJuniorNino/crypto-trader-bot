cmake_minimum_required(VERSION 3.31)
project(CryptoTrader)

set(CMAKE_CXX_STANDARD 26)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories($ENV{CPP_INCLUDE})
link_directories($ENV{CPP_LIB})

add_library(sqlite3 STATIC "$ENV{CPP_INCLUDE}/sqlite3.c")

add_executable(CryptoTrader main.cpp)

target_link_libraries(CryptoTrader sqlite3 curl)
