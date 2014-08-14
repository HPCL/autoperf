#!/usr/bin/env python

# ACISS is still using Python 2.6.6
from optparse import OptionParser

# command line parsing

parser = OptionParser()
parser.add_option("-C", "--Config",
                  action="store", dest="cfgfile",
                  help="Specify a config file. If not specified or file "
                  "does not exist, search for .autoperf.cfg, autoperf.cfg, "
                  "~/.autoperf.cfg in order")
parser.add_option("-a", "--all",
                  action="store_true", dest="runall", default=True,
                  help="Run each experiment once. Default if no option is "
                  "given. Has no effect if '-e' is given")
parser.add_option("-e", "--exp",
                  action="append", dest="exps", metavar="EXP[@NUM]",
                  help="Run experiment EXP NUM times. This option can be "
                  "used several times and experiments will be executed in "
                  "the order they appear. [default: NUM=1]")
parser.add_option("-b", "--block",
                  action="store_true", dest="block", default=False,
                  help="Instead of exit immediately after submit the experiment "
                  "to the batch system, now block until the job is finished "
                  "[default: %default]")
parser.add_option("-c", "--check",
                  action="store_const", const="check", dest="mode",
                  help="When used with '-a' or '-e', show the status (Unknown, "
                  "Running or Finished) of those experiments instead of running them")
parser.add_option("-y", "--analyze",
                  action="store_const", const="analyze", dest="mode",
                  help="When used with '-a' or '-e', analyze those experiments "
                  "data instead of running them. The experiment must be in "
                  "'Finished' state")
parser.add_option("-i", "--insname",
                  action="store", type="string", dest="insname",
                  metavar="INSTANCE", default=None,
                  help="Use with '-c' or '-y' to specify the instance name of "
                  "the experiment. Check or analyze all instances if not specified")

(options, args) = parser.parse_args()

# now run the experiments

from autoperf.utils      import config
from autoperf.experiment import *

def parse_config():
    cfgfiles = ['.autoperf.cfg',
                'autoperf.cfg',
                os.path.expanduser('~/.autoperf.cfg')]

    if options.cfgfile is not None:
        cfgfiles.insert(0, options.cfgfile)

    for cfgfile in cfgfiles:
        try:
            config.parse(cfgfile)
        except:
            print "invalid, trying next option..."
        else:
            break

    if not config.done:
        print "*** Can not find any valid config file. Abort"
        exit(1)

def get_experiment_list(allow_dup=True):
    global options
    if options.exps is None:
        return config.get("Main.Experiments").split()
    else:
        exps = [ ]
        for expnum in options.exps:
            try:
                exp, num = expnum.split('@')
                if not allow_dup:
                    num = 1
            except ValueError:
                exp = expnum
                num = 1

            for i in range(int(num)):
                exps.append(exp)

        return exps

def run_experiments():
    exps = get_experiment_list()
    for exp in exps:
        experiment = Experiment(exp)
        experiment.setup()
        experiment.run(options.block)

        if (options.block):
            experiment.analyze()

        experiment.cleanup()

def check_an_experiment(name, insname=None):
    experiment = Experiment(name, insname, mode="check")
    experiment.setup()

    stats = experiment.check()

    experiment.cleanup()

    return stats;

def check_experiments(insname=None):
    fmtstr = "{0:20} {1:30} {2:15} {3:10}"

    print "*** Experiment status:"
    print fmtstr.format("Experiment", "Instance", "Job ID", "Status")
    print "----------------------------------------------------------------------------"

    exps = get_experiment_list(False)
    for exp in exps:
        for stat in check_an_experiment(exp, insname):
            print fmtstr.format(exp, stat['insname'], stat['job_id'], stat['stat'])

def analyze_an_experiment(name, insname=None):
    for stat in check_an_experiment(name, insname):
        if stat['stat'] != 'Finished':
            print "*** Experiment %s %s is not finished yet, ignore" % (name, insname)
        else:
            print "*** Analyzing %s %s ..." % (name, stat['insname'])
            experiment = Experiment(name, stat['insname'], mode="analyze")
            experiment.setup()
            experiment.analyze()
            experiment.cleanup()

def analyze_experiments(insname=None):
    exps = get_experiment_list()
    for exp in exps:
        analyze_an_experiment(exp, insname)

parse_config()

if options.mode is None:
    run_experiments()
elif options.mode == 'check':
    check_experiments(options.insname)
elif options.mode == 'analyze':
    analyze_experiments(options.insname)
