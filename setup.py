import os
from distutils.core import setup, Extension

PAPI    = os.getenv('PAPI', '/usr/local/packages/papi/5.0.1')
GMP     = os.getenv('GMP', '/usr/local/packages/gmp/5.0.5')
SQLITE3 = os.getenv('SQLITE3', os.environ['HOME']+'/prefix/sqlite-3.8.5')

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
                        sources              = ['ext/partitioner.cpp'],
                        language             = 'c++',
                        include_dirs         = [PAPI    + '/include',
                                                GMP     + '/include',
                                                SQLITE3 + '/include'],
                        library_dirs         = [PAPI    + '/lib',
                                                GMP     + '/lib',
                                                SQLITE3 + '/lib'],
                        libraries            = ['papi', 'gmp', 'sqlite3'],
                        runtime_library_dirs = [PAPI    + '/lib',
                                                GMP     + '/lib',
                                                SQLITE3 + '/lib'],
                        define_macros        = [('EXT_PYTHON', None)],
                        extra_compile_args   = ['-Wall', '-Wno-write-strings'])

setup(
    name             = "autoperf",
    version          = "0.1.0",
    author           = "Ender Dai",
    author_email     = "xdai@uoregon.edu",
    packages         = py_packages,
    package_data     = {"autoperf.analyses": ["scripts/*.sh", "scripts/*.py"]},
    scripts          = ["bin/autoperf"],
    ext_modules      = [partitioner],
    license          = "BSD",
    description      = "Automation for experiment, perf and analysis",
    )
