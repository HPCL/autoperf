import os
from distutils.core import setup, Extension

# where to find headers/libraries to compile the extension
CUDA    = os.getenv('CUDA')
PAPI    = os.getenv('PAPI', '/usr/local/packages/papi/5.0.1')

INCLUDE_DIRS  = [PAPI    + '/include']
LIBRARY_DIRS  = [PAPI    + '/lib', PAPI + '/lib64']
LIBRARIES     = ['papi']
DEFINE_MACROS = [('EXT_PYTHON', None)]

if CUDA is not None:
    INCLUDE_DIRS.extend([CUDA + '/include',
                         CUDA + '/extras/CUPTI/include'])
    LIBRARY_DIRS.extend([CUDA + '/lib64',
                         CUDA + '/extras/CUPTI/lib64'])
    LIBRARIES.extend(['cuda', 'cudart', 'cupti'])
    DEFINE_MACROS.append(('WITH_CUPTI', None))

# get the name of all python packages
py_packages = []
cur_dir = os.getcwd()
src_dir = os.path.join(cur_dir, 'autoperf')
for root, dirs, files in os.walk(src_dir, topdown=True):
    if '__init__.py' in files:
        rel_dir = root[len(cur_dir)+1:]
        dir_names = rel_dir.split(os.sep)
        py_packages.append('.'.join(dir_names))

# partitioner is a python extension written in c++
partitioner = Extension(name                 = 'autoperf.partitioner',
                        sources              = ['ext/partitioner.cpp', 'ext/sqlite3.c'],
                        language             = 'c++',
                        include_dirs         = INCLUDE_DIRS,
                        library_dirs         = LIBRARY_DIRS,
                        libraries            = LIBRARIES,
                        runtime_library_dirs = LIBRARY_DIRS,
                        define_macros        = DEFINE_MACROS,
                        extra_compile_args   = ['-Wall', '-Wno-write-strings'])

setup(
    name             = "autoperf",
    version          = "0.1.0",
    author           = "Ender Dai",
    author_email     = "xdai@uoregon.edu",
    packages         = py_packages,
    package_data     = {"autoperf.utils": ["scripts/*.sh", "scripts/*.py"],
			"autoperf.utils.metric_spec": ["*"]},
    scripts          = ["bin/autoperf"],
    ext_modules      = [partitioner],
    license          = "BSD",
    description      = "Automation for experiment, perf and analysis",
    )
