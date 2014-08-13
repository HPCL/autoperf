import os
from setuptools import setup, find_packages, Extension

PAPI    = os.getenv('PAPI', '/usr/local/packages/papi/5.0.1')
GMP     = os.getenv('GMP', '/usr/local/packages/gmp/5.0.5')
SQLITE3 = os.getenv('SQLITE3', os.environ['HOME']+'/prefix/sqlite-3.8.5')

partitioner = Extension(name                 = 'partitioner',
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
    packages         = find_packages(),
    scripts          = ["bin/perf.py"],
    ext_modules      = [partitioner],
    license          = "BSD",
    description      = "Automation for experiment, perf and analysis",
    )
