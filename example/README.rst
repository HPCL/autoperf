========
Examples
========
This directory contains several examples which help you to quickly
learn how to use the *autoperf*. We suggest you go through the
examples in the order below::

  helloworld     -- the simplest, most basic example
  mpi            -- working with a MPI application
  hpctoolkit     -- use hpctoolkit as the performance tool
  derived        -- how to define more than one examples in one config file

Note that those examples do not show all the config options. For a full
list of the options and their explanation, see below.

Config file syntax
===================

Generic
-------
The config file is parsed with Python module "ConfigParser". So all
rules specified in

  https://docs.python.org/2/library/configparser.html

also apply here. Basically, it looks pretty much like the classic .ini
files.

Any option the name of which starts with a capital letter is a
**Derive Name**. The values of the **Derive Name** are **Derive
Key**. The **Derive Name** itself is a valid section name known as the
**Base Section**.

The derive key of a derive name "Name" will be referred as "$Name" in
this document.

New sections can be drived from **Base Section** and **Derive Key**
using some predefined pattern. The pattern is called the **fullname**
of the **Base Section**.

For example, in following config snippet::

  [Main]
  Experiments = exp1 exp2 exp3

the option "Experiments" is a derive name. "exp1", "exp2" and "exp3"
are three derive keys. $Experiments is "exp1" or "exp2" or"exp3". As
the **fullname** of section "Experiments" is
"Experiments.$Experiments" (see below), following section names are
all valid::

  [Experiments]         -- Base Section
  [Experiments.exp1]    -- Derived Section
  [Experiments.exp2]    -- Derived Section
  [Experiments.exp3]    -- Derived Section

For any defined experiment and a section "Section" with the fullname
"Section.$Derive1.$Derive2.$Derive3", in order to get an option
"Option" under the section, it will search for "Option" under the
following sections in order. The first "Option" it find will be used.::

  [Section.$Derive1.$Derive2.$Derive3]
  [Section.$Derive1.$Derive2]
  [Section.$Derive1]
  [Section]

Thus, this essentially creates hierarchy between sections, almost like
the idea of "supper class" and "sub class".

Valid options
-------------

Main
~~~~
Purpose

  This is the entrance of the config file.

Fullname

  Main

Options

  Experiments

    value: a list of string

    meaning: names of the experiments we are defining

    mandatory: yes

Experiments
~~~~~~~~~~~
Purpose

  This is where you define a specific experiment.

Fullname

  Experiments.$Experiments

Options

  rootdir

    value: a string

    meaning: a path name, used as cwd of *autoperf*, base directory of
    all relative path used in config file

    mandatory: no

    default: current working directory

  tauroot

    value: a string

    meaning: <tauroot>/lib and <tauroot>/bin will be searched for TAU
    librires and binaries

    mandatory: yes

  cupti

    value: "yes" or "no"

    meaning: use CUPTI or not

    mandatory: no

    default: "no"

  launcher

    value: a string

    meaning: a program used to launch the user application

    mandatory: no

    default: "aprun" for NERSC systems, empty for others

  launcher_opts

    value: a string

    meaning: command line options for application launcher

    mandatory: no

    default: empty

  copy:

    value: a list of string

    meaning: a list of files/directories that will be copied to
    *rootdir* before the experiment get running

    mandatory: no

    default: no default value
  
  link

    value: a list of string

    meaning: a list of files/directories that will be "ln -s" to
    *rootdir* before the experiment get running
    
    mandatory: no

    default: no default value

  execmd

    value: a string

    meaning: path to the application you are working on

    mandatory: yes

  exeopt

    value: a string

    meaning: cmdline options for *execmd*

    mandatory: no

    default: no default value

  builder

    value: a string

    meaning: a command line get running before experiment starting,
    can be used to build the application
    
    mandatory: no

    default: no default value

  Platform

    value: "generic", "aciss" or "hopper"

    meaning: the platform we are using

    mandatory: no

    default: "generic"

  Tool

    value: "tau" or "hpctoolkit"

    meaning: the tool used to collect performance data

    mandatory: no

    default "tau"

  Datastore

    value: "nop" or "taudb"

    meaning: where to save the performance data

    meandatory: no

    default: "nop"

  Analyses

    value: list of "metrics", "gensel"

    meanling: list of analysis we need to perform on performance data

    mandatory: yes

Platform
~~~~~~~~
Purpose

  This is where you give some platform specific options.

Fullname

  Platform.$Platform.$Experiments

Options

  Queue

    value: "serial", "PBS" or "mic"

    meaning: the batch system we are going to use. Chosse "serial" if
    do not use any batch system. "mic" is used to run MIC native
    application.
    
    mandatory: no

    default: "serial"

Queue
~~~~~
Purpose

  This is where you specify options to the batch system.

Fullname

  Queue.$Queue.$Platform.$Experiments

Options for Queue.PBS

  options

    value: newline splited string

    meaning: options for PBS script, e.g. "-q short"

    mandatory: no

    default: your PBS system default

Tool
~~~~
Purpose

  This is where you specify options to the performance tool.

Fullname

  Tool.$Tool.$Experiments

Options for Tool.tau

  mode

    value: "sampling" or "instrumentation"

    meaning: use sampling or instrumentation

    mandatory: no

    default: "sampling"

  period

    value: a number

    meaning: use when *mode* is "sampling"; "-ebs_period" option for "tau_exec"

    mandatory: no

    default: 10000

  source

    value: a string

    meaning: use when *mode* is "sampling"; "-ebs_source" option for "tau_exec"

    mandatory: no

    default: "TIME"

  TAU_MAKEFILE

    value: a string

    meaning: use when *[Experiments].builder* is specified; a relative
    path to *<[Experiments].tauroot>*/lib

    mandatory: no

    default: *<[Experiments].tauroot>*/lib/Makefile.tau-papi-mpi-pdt

  Any TAU variables

    value: depends on the variable

    meaning: depends on the variable

    mandatory: no

    default: depens on the variable

Options for Tool.hpctoolkit

  appsrc

    value: a string

    meaning: path to the source of your application

    meandatory: yes

Datastore
~~~~~~~~~
Purpose

  This is where you set parameters to a specific datastore

Fullname:

  Datastore.$Datastore.$Experiments

Options for Datastore.taudb

  config

    value: a string

    meaning: name of the taudb configuration

    mandatory: yes

Analyses
~~~~~~~~
Purpose

  This is where you set parameters to a specific analysis

Fullname

  Analyses.$Analyses.$Experiments

Options for Analyses.metrics

  metrics

    value: a list of strings

    meaning: a list of counters we need to collect

    mandatory: yes

  derived_metrics

    value: a list of strngs

    meaning: a list of the name of derived metrics, must provide definitions

    mandatory: no

    default: no default value

  derived metric name

    value: a string

    meaning: an arithmetic expression, use *metrics* to define *derived_metrics*

    mandatory: yes if *derived_metrics* is defined

    default: no default value

Env
~~~
Purpose

  All name/value pairs in this section are set as environment variable
  for the experiment.

Fullname

  Env.$Experiments

Metadata
~~~~~~~~
Purpose

  All name/value pairs in this section will be added into "-y"
  generated PPK file as metadata.

Fullname

  Metadata.$Experiments
