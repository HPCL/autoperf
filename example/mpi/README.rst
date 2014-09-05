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

[Experiments].mpi
-----------------
This tells *autoperf* that it's working on some MPI application.::

  [Experiments]
  ...
  ...
  mpi = yes
  ...
  ...

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
  nodes     = 2
  ppn       = 12
  walltime  = 4:00:00
  pmem      = 1gb
  queuename = short

[Analyses.metrics].derived_metrics
----------------------------------
You can define some derived metrics based on regular metrics. First,
specify regular metrics you want to collect::

  [Analyses.metrics]
  metrics = PAPI_FP_INS PAPI_TOT_INS PAPI_RES_STL PAPI_TOT_CYC
            PAPI_L1_DCM PAPI_L1_ICM PAPI_L2_DCM PAPI_L2_ICM
            PAPI_L1_TCM PAPI_L2_TCM PAPI_L3_TCM

Next, name the derived metrics you need::

  derived_metrics = FP_INEFFICIENT2

At last, you need to give your derived metric its definition::

  FP_INEFFICIENT2 = ((PAPI_FP_INS/PAPI_TOT_INS)*(PAPI_RES_STL/PAPI_TOT_CYC))*(PAPI_TOT_CYC/2075051737)
