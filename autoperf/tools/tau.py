import os
import subprocess, tempfile
import ConfigParser

from ..utils import config
from .interface import *

class Tool(AbstractTool):
    def __init__(self, experiment):
        self.name       = "tau"
        self.longname   = "Tool.tau.%s" % experiment.name
        self.experiment = experiment
        self.ppk        = "%s.%s.ppk" % (experiment.name, experiment.insname)
        self.profiledir = experiment.insname

    def build(self):
        print "Building TAU..."

    def setup(self):
        self.platform = self.experiment.platform
        self.analyses = self.experiment.analyses

        if not os.path.isdir(self.profiledir):
            os.makedirs(self.profiledir)

        self.metrics = [ ]
        for analysis in self.analyses.values():
            self.metrics += analysis.metrics

    def setup_str(self):
        tau_setup   = ""
        tau_options = config.get(self.longname)
        for option in tau_options:
            # take all upper case options as TAU environment variables
            if option.upper() == option:
                tau_setup += "export %s=%s\n" % (option, tau_options[option])

        tau_setup += "export TAU_METRICS=%s\n" % ":".join(self.metrics)
        tau_setup += "export PROFILEDIR=%s\n" % self.profiledir
        return tau_setup

    def wrap_command(self, execmd, exeopt):
        mode = config.get("%s.mode" % self.longname)

        if mode == "instrumentation":
            return [execmd, exeopt]

        if mode == "sampling":
            try:
                period = config.get("%s.period" % self.longname)
            except ConfigParser.Error:
                period = 10000

            try:
                source = config.get("%s.source" % self.longname)
            except ConfigParser.Error:
                source = TIME

            return ["tau_exec -ebs -ebs_period=%s -ebs_source=%s %s " % (period, source, execmd), exeopt]

    def collect_data(self):
        process = subprocess.Popen(["paraprof", "--pack", self.ppk, self.profiledir],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()

    def analyze(self):
        this_dir, this_file = os.path.split(__file__)
        for analysis in self.analyses.values():
            f = open("%s/perfexplorer/%s.py" % (this_dir, analysis.name), "r")
            script = f.read().format(
                TAULIB          = config.get("%s.TAULIB" % self.longname),
                ppk             = self.ppk,
                derived_metrics = repr(analysis.derived_metrics)
                )

            analyzer = open("%s.py" % analysis.name, 'w')
            analyzer.write(script)
            analyzer.close()
            os.chmod("%s.py" % analysis.name, 0755)
            subprocess.call("./%s.py" % analysis.name)
            
