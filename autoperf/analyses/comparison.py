import os
import re

from ..utils    import config
from .interface import AbstractAnalysis

class Analysis(AbstractAnalysis):

    def __init__(self, experiment):
        self.name       = "comparison"
        self.longname   = "Analyses.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        self.longmetrics = config.get("%s.metrics" % self.longname, "TIME").split()
        self.metrics     = self.longmetrics

        self.mode      = config.get("%s.mode"      % self.longname, "absolute")
        self.throttle  = config.get("%s.throttle"  % self.longname, 1000)
        self.threshold = config.get("%s.threshold" % self.longname, 10)
        self.base      = config.get("%s.base"      % self.longname)

    def setup(self):
        self.aName     = config.get("%s.instance"  % self.longname, "last")

        instances = self.get_all_instance(self.base)
        if len(instances) == 0:
            raise Exception("Can not find any instance of experiment '%s'" % self.base)

        if self.aName == "last":
            self.aName, self.aDir = instances[-1]
        else:
            for n, d in instances:
                if self.aName == n:
                    self.aDir = d
                    break

    def get_all_instance(self, expname):
        """
        Get all instances of an experiment.

        Args:
          expname (string): Name of an experiment

        Returns:
          list: A list of (instance_name, data_directory)
        """
        instances = [ ]

        rootdir = config.get("Experiments.%s.rootdir" % expname,
                             self.experiment.cwd)
        rootdir = os.path.join(self.experiment.cwd, rootdir)

        dirs = [os.path.join(rootdir, f) for f in os.listdir(rootdir)]
        dirs = [d for d in dirs if os.path.isdir(d)]
        for dirname in dirs:
            if not re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}T\d{3}",
                            os.path.basename(dirname)):
                continue

            status = "%s/job.stat" % dirname
            if not os.path.isfile(status):
                continue

            fp = open(status, 'r')
            stat = fp.read().split()
            fp.close()

            if stat[0] == expname:
                instances.append((os.path.basename(dirname), dirname))

        instances.sort(key = lambda inst: inst[0])

        return instances

    def run(self):
        self.bName  = self.experiment.insname
        self.bDir   = os.path.join(os.getcwd(), self.bName)

        # cwd = os.getcwd()
        # os.chdir(self.experiment.insname)
        self.run_script("%s.py" % self.name,
                        tauroot   = self.experiment.tauroot,
                        aName     = self.aName,
                        aDir      = self.aDir,
                        bName     = self.bName,
                        bDir      = self.bDir,
                        metrics   = self.metrics,
                        mode      = self.mode,
                        throttle  = self.throttle,
                        threshold = self.threshold,
                        taudb     = self.experiment.datastore.config
                        )
        # os.chdir(cwd)
