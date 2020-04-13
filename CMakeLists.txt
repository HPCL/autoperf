cmake_minimum_required(VERSION 3.1 FATAL_ERROR)
project(autoperf LANGUAGES CXX C)


# Version information
set(AUTOPERF_MAJOR_VERSION 1)
set(AUTOPERF_MINOR_VERSION 0)
set(AUTOPERF_PATCH_VERSION 0)
set(AUTOPERF_VERSION "${AUTOPERF_MAJOR_VERSION}.${AUTOPERF_MINOR_VERSION}.${AUTOPERF_PATCH_VERSION}-dev")

# Configuration options
option(WITH_MPI       "Enable MPI" FALSE)
option(WITH_PAPI      "Enable PAPI hardware counter service (requires papi)" FALSE)
option(WITH_TAU       "Enable TAU service (TAU Performance System)" FALSE)
#option(WITH_AUTOPERF   "Enable Autoperf service" FALSE)

# Add our module directory to the include path.
set(CMAKE_MODULE_PATH "${PROJECT_SOURCE_DIR}/cmake;${CMAKE_MODULE_PATH}")


# cmake v. < 3.12
find_package(PythonInterp 3 REQUIRED)
find_package(CUDA QUIET)

# Newer way requires cmake v. >= 3.12
# find_package (Python3 COMPONENTS Interpreter Development)

# Find MPI
if (WITH_MPI)
  find_package(MPI)
  if (MPI_C_FOUND)
    set(AUTOPERF_HAVE_MPI TRUE)
    set(AUTOPERF_MPI_CMAKE_MSG "Yes, using ${MPI_C_LIBRARIES}")

    if (WITH_MPIT)
      message(STATUS "MPIT is currently not supported, disabling.")
      # set(AUTOPERF_HAVE_MPIT TRUE)
      # set(AUTOPERF_MPIT_CMAKE_MSG "Yes")
    endif()

    if (AUTOPERF_HAVE_GOTCHA)
      set(AUTOPERF_MPIWRAP_USE_GOTCHA TRUE)
      set(AUTOPERF_MPIWRAP_CMAKE_MSG "Yes, using GOTCHA")
    else()
      set(AUTOPERF_MPIWRAP_CMAKE_MSG "Yes, using PMPI")
    endif()
  endif()
endif()

# Find PAPI
if (WITH_PAPI)
  include(FindPAPI)
  if (PAPI_FOUND)
    set(AUTOPERF_HAVE_PAPI TRUE)
    set(AUTOPERF_PAPI_CMAKE_MSG "Yes, using ${PAPI_LIBRARIES}")
    list(APPEND AUTOPERF_EXTERNAL_LIBS ${PAPI_LIBRARIES})
  else()
    message(WARNING "PAPI support was requested but PAPI was not found!\n"
  "Set PAPI_PREFIX to the PAPI installation path and re-run cmake.")
  endif()
endif()




# -----------------------------------------------------------------

# Extra gprof helper to enable profiling of multithreaded codes
add_library(gprof-helper SHARED ext/gprof-helper.c)

# Handle various options
if(WITH_TAU)
  if (AUTOPERF_HAVE_MPI)
    find_package(TAU QUIET)
    if (TAU_FOUND)
      set(AUTOPERF_HAVE_TAU TRUE)
      set(AUTOPERF_TAU_CMAKE_MSG "Yes, using ${TAU_LIBRARIES}")
      list(APPEND AUTOPERF_MPI_EXTERNAL_LIBS ${TAU_LIBRARIES})
    else()
      message(WARNING "TAU bindings requested but TAU API was not found!\n"
        "Set TAU_PREFIX to installation path and re-run cmake.")
    endif()
  else()
    message(WARNING "TAU support requires MPI-enabled build!\n")
  endif()
endif()



# ---- The actual implementation setuputils build and installation: ----

# Python configuration and setup
set(SETUP_PY_IN "${CMAKE_CURRENT_SOURCE_DIR}/setup.py.in")
set(SETUP_PY    "${CMAKE_CURRENT_BINARY_DIR}/setup.py")
set(DEPS        "${CMAKE_CURRENT_SOURCE_DIR}/autoperf/__init__.py")
set(OUTPUT      "${CMAKE_CURRENT_BINARY_DIR}/build/")
set(PAPI        "${PAPI_PREFIX}")
set(CUDA        "${CUDA_TOOLKIT_ROOT_DIR}")

configure_file(${SETUP_PY_IN} ${SETUP_PY})

add_custom_command(OUTPUT ${OUTPUT}
                   COMMAND ${PYTHON_EXECUTABLE} ${SETUP_PY} build
                   COMMAND ${CMAKE_COMMAND} -E touch ${OUTPUT}
                   DEPENDS ${DEPS})

add_custom_target(target ALL DEPENDS ${OUTPUT})

install(CODE "execute_process(COMMAND ${PYTHON_EXECUTABLE} ${SETUP_PY} install --prefix=${CMAKE_INSTALL_PREFIX})")


#
# Print config summary
#

message(STATUS "Autoperf configuration summary:")

message(STATUS "Autoperf version          : ${AUTOPERF_VERSION}")
message(STATUS "Build type                : ${CMAKE_BUILD_TYPE}")
message(STATUS "Python interpreter        : ${PYTHON_EXECUTABLE}")
message(STATUS "Python version            : ${PYTHON_VERSION_STRING}")
message(STATUS "Compiler                  : ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION} (${CMAKE_CXX_COMPILER})")
message(STATUS "CUDA                      : ${CUDA_TOOLKIT_ROOT_DIR}")
message(STATUS "System                    : ${CMAKE_SYSTEM} (${CMAKE_SYSTEM_PROCESSOR})")
message(STATUS "Install dir               : ${CMAKE_INSTALL_PREFIX}")

set(AUTOPERF_MODULES
  PAPI
  MPI
  CUpti
  TAU)

foreach(_autoperf_module ${AUTOPERF_MODULES})
  string(LENGTH "${_autoperf_module}" _strlen)
  string(SUBSTRING "                " ${_strlen} "-1" _padding)
  set(_prefix "${_autoperf_module} support ${_padding}")

  if (DEFINED AUTOPERF_${_autoperf_module}_CMAKE_MSG)
    message(STATUS "${_prefix} : ${AUTOPERF_${_autoperf_module}_CMAKE_MSG}")
  else()
    message(STATUS "${_prefix} : No")
  endif()
endforeach()
