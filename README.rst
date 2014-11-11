========
Autoperf
========

Autoperf is a tool for creating and managing performance experiments,
including data post processing and analysis. It provides a simple
format for defining the experiment environment and data to be
collected, and interfaces to a variety of performance tools (e.g., TAU
and HPCToolkit) to perform the measurements and subsequent
analyses. The current capabilities include the collection of detailed
hardware performance counters, derived performance metrics
computations, statistical analysis, and preliminary support for
comparisons of different code versions.

Directory Structure
===================
::

  autoperf/      -- the autoperf python package
  bin/           -- directory which holds the driver script
  example/       -- an usage example
  ext/           -- c/c++ extension for python
  README.rst     -- this file


Install
===================

You can install this package following distutils convention. For
example, in order to install in your home directory::

  $ python setup.py install --user

Or, install to a specific directory::

  $ python setup.py install --prefix=<some_directory>

Read this if you want to know more about distutils:

  https://docs.python.org/2/install/index.html

The C extension in this package requires headers and libraries of
PAPI/GMP/SQLITE3 to compile. You may need to point out where to find
those using environment variables *PAPI*, *GMP* and *SQLITE3*. 

Autoperf also supports CUDA/CUPTI. To enable this feature, set
environment variable *CUDA* to the CUDA installation directory on your
system.

If it is not clear how to set those variables, read **setup.py**.

If you don't want to re-install the package after each "git pull", you
can simply do this::

  $ python setup.py build_ext -i

Now you can use autoperf in-place without installation. However, if
ext/ is updated in "git pull", you must rebuild it using the command
above.

Usage
===================
Several examples are provided under *example/*.  A config file,
*autoperf.cfg*, is provided for each example.

The config file can be specified though command line option. If not
specified, autoperf will search for the first valid file in the order
below::

  .autoperf.cfg : autoperf.cfg : ~/.autoperf.cfg

A driver script named "autoperf" is included in *bin/*. Run the driver
script to execute the experiments and collect the data::

  $ autoperf -h
  Usage: autoperf [options]

  Options:
    -h, --help            show this help message and exit
    -f CFGFILE, --config=CFGFILE
                          Specify a config file. If not specified or file does
                          not exist, search for .autoperf.cfg, autoperf.cfg,
                          ~/.autoperf.cfg in order
    -a, --all             Run each experiment once. Default if no option is
                          given. Has no effect if '-e' is given
    -e EXP[@NUM], --exp=EXP[@NUM]
                          Run experiment EXP NUM times. This option can be used
                          several times and experiments will be executed in the
                          order they appear. [default: NUM=1]
    -b, --block           Instead of exit immediately after submit the
                          experiment to the batch system, now block until the
                          job is finished [default: False]
    -c, --check           When used with '-a' or '-e', show the status (Unknown,
                          Running or Finished) of those experiments instead of
                          running them
    -y, --analyze         When used with '-a' or '-e', analyze those experiments
                          data instead of running them. The experiment must be
                          in 'Finished' state
    -i INSTANCE, --insname=INSTANCE
                          Use with '-c' or '-y' to specify the instance name of
                          the experiment. Check or analyze all instances if not
                          specified


Thus, you could try::

  $ autoperf

or::

  $ autoperf -e pi_tau_inst -e pi_tau_samp@5

Note that this will just submit the job to batch system (maybe
PBS). You can check whether the job has been finished with::

  $ autoperf -c

If the job is finished, you can analyze collected data with::

  $ autoperf -y

Or, you can do the job submission and data analyze in one step::

  $ autoperf -b

In this case, the script will not return until the job is finished and
the analysis is done. After the driver script returns, you can find
collected data under *output/*. The data is also loaded into taudb if
"Datastore=taudb" is specified in config file. In such case,You can
run *paraperf* to check the data.
