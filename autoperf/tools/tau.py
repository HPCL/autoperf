import os
import subprocess
import ConfigParser

from ..utils import config
from .interface import *

class Tool(AbstractTool):
    def __init__(self, experiment):
        self.name       = "tau"
        self.longname   = "Tool.tau.%s" % experiment.name
        self.experiment = experiment

    def setup(self):
        self.platform = self.experiment.platform
        self.analyses = self.experiment.analyses

    def build_env(self):
        tau_makefile = config.get("%s.TAU_MAKEFILE" % self.longname,
                                  "%s/lib/Makefile.tau-papi-mpi-pdt" % self.experiment.tauroot)

        try:
            selfile = config.get("%s.selfile" % self.longname)
        except ConfigParser.Error:
            tau_options = os.getenv("TAU_OPTIONS", "")
        else:
            selfile = os.path.abspath(selfile)
            tau_options = "%s -optTauSelectFile=%s" % (os.getenv("TAU_OPTIONS", ""), selfile)

        env = {
            'TAU_ROOT'    : self.experiment.tauroot,
            'TAU_MAKEFILE': tau_makefile,
            'TAU_OPTIONS' : tau_options
            }

        return env

    def setup_str(self):
        tau_setup   = "mkdir -p %s\n" % self.experiment.insname
        tau_options = config.get_section(self.longname)
        for name, value in tau_options:
            # take all upper case options as TAU environment variables
            if name.upper() == name:
                tau_setup += "export %s=%s\n" % (name, value)

        part = int(self.experiment.insname[27:])

        tau_setup += "export TAU_METRICS=%s\n" % self.experiment.parted_metrics[part]
        tau_setup += "export PROFILEDIR=%s\n" % self.experiment.insname
        return tau_setup

    def wrap_command(self, execmd, exeopt):
        mode = config.get("%s.mode" % self.longname, "sampling")

        if mode == "instrumentation":
            return [execmd, exeopt]

        if mode == "sampling":
            period = config.get("%s.period" % self.longname, 10000)
            source = config.get("%s.source" % self.longname, "TIME")

            if self.experiment.is_mpi:
                mpi = "-T MPI"
            else:
                mpi = "-T SERIAL"

            return ["tau_exec %s -ebs -ebs_period=%s -ebs_source=%s %s " % (mpi, period, source, execmd), exeopt]

        raise Exception("TAU: invalid mode: %s. (Available: instrumentation, sampling)" % mode)

    def collect_data(self):
        process = subprocess.Popen(["paraprof",
                                    "--pack",
                                    "%s.ppk" % self.experiment.insname,
                                    self.experiment.insname],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()

