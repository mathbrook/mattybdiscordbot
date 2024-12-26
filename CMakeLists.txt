cmake_minimum_required(VERSION 3.14)

# Project name and version
project(DiscordBot VERSION 1.0 LANGUAGES CXX)

# Specify C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Add the executable
add_executable(DiscordBot src/main.cpp)

# Find and link the D++ library (DPP)
find_package(dpp REQUIRED)

# Include nlohmann/json library (assumes it's installed with vcpkg or is available as a header-only library)
find_package(nlohmann_json REQUIRED)

# Link libraries to the executable
target_link_libraries(DiscordBot PRIVATE dpp::dpp nlohmann_json::nlohmann_json)

# Include directories if needed (optional for DPP or JSON if they aren't automatically handled by find_package)
target_include_directories(DiscordBot PRIVATE ${DPP_INCLUDE_DIRS} ${NLOHMANN_JSON_INCLUDE_DIRS})

# Compiler warnings (optional)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(DiscordBot PRIVATE -Wall -Wextra -pedantic)
elseif(CMAKE_CXX_COMPILER_ID MATCHES "MSVC")
    target_compile_options(DiscordBot PRIVATE /W4 /permissive-)
endif()