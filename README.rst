========
Autoperf
========

Directory Structure
===================
::

  autoperf/      -- the autoperf python package
  bin/           -- directory which holds the driver script
  example/       -- a usage example
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

Later we may provide some way so the user could designate a config
file explicitly. But for now, the config file is searched in following
sequence::

  .autoperf.cfg : autoperf.cfg : ~/.autoperf.cfg

Note that for now you must setup a taudb config before autoperf could
work. We will remove this hard coded dependence soon. To create a
taudb config::

  $ module load tau
  $ perfdmf_configure

Make sure the name of the config you choose is the same as what is
*autoperf.cfg*. *autoperf.cfg* is self documented and you may want to
read it through.

Now you can run the driver script to execute the experiments and
collect the data::

  $ ../bin/perf.py -h
  Usage: perf.py [options]
  
  Options:
    -h, --help            show this help message and exit
    -a, --all             Run each experiment once. Default if no option is
                          given. Has no effect if '-e' is given
    -e EXP[@NUM], --exp=EXP[@NUM]
                          Run experiment EXP NUM times. This option can be used
                          several times and experiments will be executed in the
                          order they appear. [default: NUM=1]

Thus, you could try::

  $ ../bin/perf

or::

  $ ../bin/perf -e pi_tau_inst -e pi_tau_samp@5

After the driver script returns, you can find collected data under
*output/*. The data is also loaded into taudb. You can run *paraperf*
to have a check.
