========
Autoperf
========

Autoperf is a tool for creating and managing performance experiments, including data post processing and analysis. It provides a simple format for defining the experiment environment and data to be collected, and interfaces to a variety of performance tools (e.g., TAU and HPCToolkit) to perform the measurements and subsequent analyses. The current capabilities include the collection of detailed hardware performance counters, derived performance metrics computations, statistical analysis, and preliminary support for comparisons of different code versions.

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
An example is included under *example/*. On ACISS::

  $ module load tau
  $ cd example
  $ export TAU_MAKEFILE=...
  $ make

The example is a naive MPI program which calculates Pi. Three targets
are defined in the makefile::

  mpi_pi: regular binary compiled with mpicc
  mpi_pi_pdt: binary build with TAU PDT based instrumentation
  mpi_pi_sel: same as mpi_pi_pdt, but with selective instrumentation

A config file, *autoperf.cfg*, is provided, which defines two
experiments, one for instrumentation, the other for sampling.

The config file could be specified though command line option. If not
specified, it will search for the first valid file in the order
below::

  .autoperf.cfg : autoperf.cfg : ~/.autoperf.cfg

Note that for now you must setup a taudb config before autoperf could
work. We will remove this hard coded dependence soon. To create a
taudb config::

  $ module load tau
  $ perfdmf_configure

Make sure the name of the config you choose is the same as what is in
*autoperf.cfg*. *autoperf.cfg* is self documented and you may want to
read it through.

Now you can run the driver script to execute the experiments and
collect the data::

  $ ../bin/autoperf -h
  Usage: autoperf [options]

  Options:
    -h, --help            show this help message and exit
    -C CFGFILE, --Config=CFGFILE
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

  $ ../bin/autoperf

or::

  $ ../bin/autoperf -e pi_tau_inst -e pi_tau_samp@5

Note that this will just submit the job to batch system (maybe
PBS). You can come back later to check whether the job has been
finished with::

  $ ../bin/autoperf -c

If the job is finished, you can analyze collected data with::

  $ ../bin/autoperf -y

Or, you can do the job submission and data analyze in one step::

  $ ../bin/autoperf -b

In this case, the script will not return until the job is finished and
the analyze is done. After the driver script returns, you can find
collected data under *output/*. The data is also loaded into
taudb. You can run *paraperf* to have a check.

The *autoperf.cfg* comes with this example defines three experiments::

  pi_tau_inst: this will use mpi_pi_pdt for instrumentation based
  profiling
  pi_tau_samp: this will use mpi_pi for sampling based profiling, a
  selective file is also generated
  pi_tau_sel: this is another instrumentation based profiling. It
  will use mpi_pi_sel which is built with the selective file generated
  with pi_tau_samp

In order to run *pi_tau_sel*, you should first run *pi_tau_samp* and
finish the analysis step, thus the selective file could be
generated. After that, *pi_tau_sel* will build *mpi_pi_sel* and run
the experiment::

  $ ../bin/autoperf -e pi_tau_samp
  $ ../bin/autoperf -e pi_tau_samp -c
  $ ../bin/autoperf -e pi_tau_samp -y

  (or, above three step in one line:
  $ ../bin/autoperf -e pi_tau_samp -b)

  $ ../bin/autoperf -e pi_tau_sel
  $ ../bin/autoperf -e pi_tau_sel -c
  $ ../bin/autoperf -e pi_tau_sel -y

  (or, above three step in one line:
  $ ../bin/autoperf -e pi_tau_sel -b)
  
Several other examples are put in the sub-directories. Check the
README.rst files there for more details.
