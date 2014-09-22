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

    def setup(self):
        self.platform = self.experiment.platform
        self.analyses = self.experiment.analyses

        self.metrics = [ ]
        for analysis in self.analyses.values():
            self.metrics += analysis.longmetrics

    def build_env(self):
        return dict()

    def setup_str(self):
        return ""

    def wrap_command(self, execmd, exeopt):
        self.measurement = "%s/measurement" % self.experiment.insname
        _execmd = "hpcrun -o %s" % self.measurement

        part = int(self.experiment.insname[27:])

        for metric in self.experiment.parted_metrics[part].split(':'):
            _execmd += " -e %s" % metric

        _execmd += " %s" % execmd

        return [_execmd, exeopt]

    def collect_data(self):
        execmd = config.get("%s.execmd" % self.experiment.longname)
        execmd = os.path.expanduser(execmd)
        exebin = os.path.basename(execmd)
        appsrc = config.get("%s.appsrc" % self.longname)

        self.measurement = "%s/measurement" % self.experiment.insname
        self.database    = "%s/database"    % self.experiment.insname
        self.hpcstruct   = "%s/%s.hpcstruct" % (self.experiment.insname, exebin)

        # do nothing if data.ppk is already there
        if os.path.isfile("%s/data.ppk" % self.experiment.insname):
            return

        subprocess.call(["hpcstruct",
                         "-o",
                         self.hpcstruct,
                         execmd])
        subprocess.call(["hpcprof",
                         "-o",
                         self.database,
                         "-S",
                         self.hpcstruct,
                         "-I",
                         "%s/'*'" % appsrc,
                         self.measurement])

        process = subprocess.Popen(["paraprof",
                                    "-f",
                                    "hpc",
                                    "--pack",
                                    "%s/data.ppk" % self.experiment.insname,
                                    "%s/experiment.xml" % self.database],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()
