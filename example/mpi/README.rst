=====
About
=====
This example show you how to use *autoperf* with MPI applications. A
simple MPI program to calculate Pi is include for demonstration.

What's New
==========

[Experiments].Platform
----------------------
As different machine or cluster could have different MPI
environment. You need to tell *autoperf* which platform it's working
on. To work on ACISS, set it as "aciss".::

  [Experiments]
  ...
  ...
  Platform = aciss
  ...
  ...

Another predefined platfomr is named "generic". As the name implies,
it makes no assumption to the software/hardware environment.

[Experiments].exeopt
--------------------
This could be used to give your application some cmdline options.::

  [Experiments]
  ...
  ...
  exeopt = 1000000
  ...
  ...

[Experiments].launcher
-----------------
This tells *autoperf* that the application shall be invoked by a launcher.
This is usually the case for MPI application. Cray also requires to launch
your applicaition (MPI or not) with "aprun".::

  [Experiments]
  ...
  ...
  launcher = mpirun
  ...
  ...

Launcher option can be specified with [Experiments].launcher_opts.

[Platform]
----------
You can specify some parameters to the platform you choose. Here we
set the batch system as "PBS".::

  [Platform]
  Queue = PBS

Another valid value for [Platform].Queue is "serial", which uses no
batch system or scheduler.

[Queue]
-------
You can give options to the batch system with this section. If none is
given, system default will be used.::

  [Queue]
  options   = -l nodes=2:ppn=12
              -l walltime=4:00:00
              -l pmem=1gb
              -q short

[Analyses.metrics].derived_metrics
----------------------------------
You can define some derived metrics based on regular metrics. Simply
put metric specification under autoperf/utils/metric_spec/ directory::

  $ cat ../../autoperf/utils/metric_spec/FP_INEFFICIENT2
  ((PAPI_FP_INS/PAPI_TOT_INS)*(PAPI_RES_STL/PAPI_TOT_CYC))*(PAPI_TOT_CYC/META_CPU_HZ)

Then you can use them as normal metrics::

  [Analyses.metrics]
  metrics = PAPI_L1_DCM FP_INEFFICIENT2
