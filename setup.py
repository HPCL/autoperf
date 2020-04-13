import os
import subprocess
from distutils.command.install import install as _install
from distutils.core import setup, Extension

# Force the use of g++ for C++ extensions
os.environ["CXX"] = "g++"

# where to find headers/libraries to compile the extension
CUDA = os.getenv('CUDA')
PAPI = os.getenv('PAPI', '/usr/local')

INCLUDE_DIRS = [PAPI + '/include']
LIBRARY_DIRS = [PAPI + '/lib', PAPI + '/lib64']
LIBRARIES = ['papi']
DEFINE_MACROS = [('EXT_PYTHON', None)]

if CUDA is not None:
    INCLUDE_DIRS.extend([CUDA + '/include', CUDA + '/extras/CUPTI/include'])
    LIBRARY_DIRS.extend([CUDA + '/lib64', CUDA + '/extras/CUPTI/lib64'])
    LIBRARIES.extend(['cuda', 'cudart', 'cupti'])
    DEFINE_MACROS.append(('WITH_CUPTI', None))

# get the names of all python packages in Autoperf
py_packages = []
cur_dir = os.getcwd()
src_dir = os.path.join(cur_dir, 'autoperf')
for root, dirs, files in os.walk(src_dir, topdown=True):
    if '__init__.py' in files:
        rel_dir = root[len(cur_dir) + 1:]
        dir_names = rel_dir.split(os.sep)
        py_packages.append('.'.join(dir_names))

# partitioner is a python extension written in C++
partitioner = Extension(
    name='autoperf.partitioner',
    language='c++',
    include_dirs=INCLUDE_DIRS,
    library_dirs=LIBRARY_DIRS,
    libraries=LIBRARIES,
    runtime_library_dirs=LIBRARY_DIRS,
    define_macros=DEFINE_MACROS,
    extra_compile_args=['-g', '-O2', '-Wall', '-Wno-write-strings', '-std=c++11'],
    sources=['ext/partitioner.cpp', 'ext/sqlite3.c'])


# Helper C library to enable use of gprof with multi-threaded codes
class install(_install):
    def run(self):
        subprocess.call(['rm', '-f', 'libgprof-helper.so'])
        subprocess.call(['make', 'libgprof-helper.so'])
        _install.run(self)


# Main setup for the python packages and extensions
setup(
    name="autoperf",
    version="0.2.0",
    author="Boyana Norris",
    author_email="brnorris03@gmail.com",
    packages=py_packages,
    # package_data={"autoperf.utils": ["scripts/*.sh", "scripts/*.py"],
    package_data={
        "autoperf.utils.metric_spec": ["*"],
        "autoperf": ['libgprof-helper.so']},
    scripts=["bin/autoperf"],
    ext_modules=[partitioner],
    license="BSD",
    description="Automation for performance experiments and analysis",
)
