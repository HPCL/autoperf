=====
About
=====
This example shows you how to define more than 1 experiments in one
single config file. It introduce the concept of "derived section".

What's New
==========

[Main].Experiments
------------------
Now we define two experiments, put their names in sequence::

  [Main]
  Experiments = pi pi_inst

[Experiemnts.pi] and [Experiments.pi_inst]
------------------------------------------

Attach the experiment name to "Experiment" with a single dot ".", we
get two derived sections, each one includes experiment specific
options. Notice that both sections defined "Tool" option, but for "pi"
experiment, the tool is "hpctoolkit", while for "pi_inst" experiment,
the tool is "tau". The "builder" for them are also different.::

  [Experiments.pi]
  Tool      = hpctoolkit
  builder   = make -C .. pi

  [Experiments.pi_inst]
  Tool      = tau
  builder   = make -C .. pi_inst

Note that "builder" is also defined under [Experiments]::

  [Experiments]
  ...
  ...
  builder = make
  ...
  ...

This definition will be override by [Experiments.pi].builder and
[Experiments.pi_inst].builder. The idea of derived section is a little
bit like "supper class" and "sub class".

[Tool.hpctoolkit] and [Tool.tau]
--------------------------------
Those two sections are derived from [Tool] using "hpctoolkit" and
"tau". They are used to specify the options for "hpctoolkit" and "tau"
respectively.::

  [Tool.hpctoolkit]
  appsrc    = ../

  [Tool.tau]
  mode        = instrumentation
  TAU_VERBOSE = 1

Also note that this time TAU will work on instrumentation mode, which
means the application binary should be pre-instrumented.
