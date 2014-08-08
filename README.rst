========
Autoperf
========

Directory Structure
===================
::

  autoperf/      -- the autoperf python package
  bin/           -- directory which holds the driver script
  example/       -- an usage example
  README.rst     -- this file


Install
===================
Under this directory, run::

  $ python setup.py develop --user

This will install autoperf in developer mode under your home
directory, which essentially setup some symbol link points to this
directory, so you can modify python code under this directory directly
and don't need to reinstall them, or worry about the PYTHONPATH.

Usage
===================
An example is included under *example/*. On ACISS::

  $ module load tau
  $ cd example
  $ make

The example is a naive MPI program which calculates Pi. Two binaries
are built: one with TAU PDT based instrumentation, the other is just a
regular binary compiled with **mpicc**. A config file, *autoperf.cfg*,
is provided, which defines two experiments, one for instrumentation,
the other for sampling.

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

  $ ../bin/perf.py -h
  Usage: perf.py [options]

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

  $ ../bin/perf.py

or::

  $ ../bin/perf.py -e pi_tau_inst -e pi_tau_samp@5

Note that this will just submit the job to batch system (maybe
PBS). You can come back later to check whether the job has been
finished with::

  $ ../bin/perf.py -c

If the job is finished, you can analyze collected data with::

  $ ../bin/perf.py -y

Or, you can do the job submision and data analyze in one step::

  $ ../bin/perf.py -b

In this case, the script will not return until the job is finished and
the analyze is done. After the driver script returns, you can find
collected data under *output/*. The data is also loaded into
taudb. You can run *paraperf* to have a check.
