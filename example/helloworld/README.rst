========
About
========
This is the helloworld, the most basic and simplest use of *autoperf*.

What's New
==========

Everything is new! To use *autoperf*, you must give it a config file
which describes the experiments you want *autoperf* to perform. The
first thing you should know is that every config file must have a
[Main] section. That's the entrance of the config file. You must give
a name to your experiment. The name could be an arbitrary string. This
is done by set the [Main].Experiments option. Here, we give our
experiment a name "helloworld".::

  [Main]
  Experiments = helloworld

The next thing is to describe your experiment. This is done using the
[Experiments] section.::

  [Experiments]

1. You may want to set a working directory to *autoperf* so it can put
all intermediate files and collected performance data there. This is
done by set [Experiments].rootdir option. This could be an absolute or
relative (to your current working directory) path. You should know
that all other relative path appears in config file are relative to
the path you set here.::

  rootdir = output

2. You need to tell *autoperf* where to find TAU libraries and
binaries. They are needed to run the analysis. Use
[Experiments].tauroot for this. <tauroot>/lib and <tauroot>/bin will
be searched.::

  tauroot = ~bnorris2/soft/tau2/x86_64/

3. You need to choose a tool that *autoperf* will used to collect
performance data. Right now, "tau" and "hpctoolkit" are
supported. This is set in option [Experiments].Tool::

  Tool = tau

4. You need to say where to save the performance data permanently. Use
[Experiments].Datastore. "taudb" is the only supported value for now.::

  Datastore = taudb

5. You need to specify which analysis you want to perform. Use
[Experiments].Analyses. "metrics" just simply dump all metrics
collected.::

  Analyses = metrics

6. At last, of course *autoperf* need to know how to run your
application. That is why we need [Experiments].execmd.::

  execmd = ../helloworld

Now, as we are using TAUdb, we need to specify which TAUdb
configuration we are going to use. We set [Datastore].config for this
purpose. Note that the config must be valid. You may need to run
"taudb_configure" to create one if you don't have any.::

  [Datastore]
  config = demo

Next, we tell TAU to use the sampling to collect performance data. We
also may need to set some TAU environment variables.::

  [Tool.tau]
  mode = sampling
  TAU_VERBOSE = 1

At last, what metrics do we want to collect? Use
[Analyses.metrics].metrics to specify a list of metrics you need.::

  [Analyses.metrics]
  metrics = PAPI_TOT_INS PAPI_TOT_CYC

That's it. We are done. Now you can use perf.py to run the helloworld
experiment.

