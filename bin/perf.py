#!/usr/bin/env python

# ACISS is still using Python 2.6.6
from optparse import OptionParser

# command line parsing

parser = OptionParser()
parser.add_option("-a", "--all",
                  action="store_true", dest="runall", default=True,
                  help="Run each experiment once. Default if no option is "
                  "given. Has no effect if '-e' is given")
parser.add_option("-e", "--exp",
                  action="append", dest="exps", metavar="EXP[@NUM]",
                  help="Run experiment EXP NUM times. This option can be "
                  "used several times and experiments will be executed in "
                  "the order they appear. [default: NUM=1]")

(options, args) = parser.parse_args()

# now run the experiments

from autoperf.utils      import config
from autoperf.experiment import *

if options.exps is None:
    # run each experiment once
    for exp in config.get("Main.Experiments").split():
        experiment = Experiment(exp)
        experiment.setup()
        experiment.run()
        experiment.analyze()
        experiment.cleanup()
else:
    # run experiments specified on command line
    for expnum in options.exps:
        try:
            exp, num = expnum.split('@')
        except ValueError:
            exp = expnum
            num = 1
        finally:
            for i in range(int(num)):
                experiment = Experiment(exp)
                experiment.setup()
                experiment.run()
                experiment.analyze()
                experiment.cleanup()

