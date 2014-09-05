=====
About
=====
This example shows you how to use hpctoolkit to collect performance
data.

What's New
==========

[Experiments].Tool
------------------
Here we specify the tool we are going to use is "hpctoolkit"::

  [Experiments]
  ...
  ...
  Tool = hpctoolkit
  ...
  ...

[Experiments].builder
---------------------
This is a command line that will be executed before the experiment
get running. You can put anything that is a valid command here,
including user scripts. Here we just use the "make"::

  [Experiments]
  ...
  ...
  builder = make -C .. pi
  ...
  ...

[Tool.hpctoolkit]
-----------------
This is where you give hpctoolkit its options. The only thing it needs
for now is where to find your application's source code.::

  [Tool.hpctoolkit]
  appsrc = ../

[Analyses.metrics]
------------------
Not a big difference, but in hpctoolkit, you can specify the sampling
interval for each metric::

  [Analyses.metrics]
  metrics = PAPI_TOT_INS@150000 PAPI_TOT_CYC@250000

