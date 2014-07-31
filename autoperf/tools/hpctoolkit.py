import os
import subprocess
import ConfigParser

from ..utils import config
from .interface  import *

class Tool(AbstractTool):
    def __init__(self, experiment):
        self.name        = "hpctoolkit"
        self.longname    = "Tool.hpctoolkit.%s" % experiment.name
        self.experiment  = experiment
        self.measurement = "hpctoolkit-%s-measurements-%s"

        try:
            self.profiledir = config.get("%s.PROFILEDIR" % self.longname)
        except ConfigParser.Error:
            self.profiledir = 'profiles'

    def build(self):
        print "Building HPCToolkit..."

    def setup(self):
        self.platform = self.experiment.platform
        self.analyses = self.experiment.analyses

        self.metrics = [ ]
        for analysis in self.analyses.values():
            self.metrics += analysis.metrics

    def setup_str(self):
        return ""

    def wrap_command(self, execmd, exeopt):
        _execmd = "hpcrun"

        for metric in self.metrics:
            _execmd += " -e %s" % metric

        _execmd += " %s" % execmd

        return [_execmd, exeopt]

    def collect_data(self):
        execmd = config.get("%s.execmd" % self.experiment.longname)
        execmd = os.path.expanduser(execmd)
        exebin = os.path.basename(execmd)
        appsrc = config.get("%s.appsrc" % self.longname)

        self.measurement = "hpctoolkit-%s-measurements-%s" % (exebin, self.platform.queue.job_name)

        subprocess.call(["hpcstruct", execmd])
        subprocess.call(["hpcprof",
                         "-S",
                         "%s.hpcstruct" % exebin,
                         "-I",
                         "%s/'*'" % appsrc,
                         self.measurement])

        self.database = "hpctoolkit-%s-database-%s" % (exebin, self.platform.queue.job_name)
            
    def analyze(self):
        pass
