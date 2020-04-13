import os

from .interface import AbstractAnalysis
from ..utils import config


class Analysis(AbstractAnalysis):

    def __init__(self, experiment):
        self.name = "comparison"
        self.longname = "Analyses.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        self.longmetrics = config.get("%s.metrics" % self.longname, "TIME").split()
        self.metrics = [m.partition('@')[0] for m in self.longmetrics]

        self.mode = config.get("%s.mode" % self.longname, "absolute")
        self.throttle = config.get("%s.throttle" % self.longname, 1000)
        self.threshold = config.get("%s.threshold" % self.longname, 10)
        self.base = config.get("%s.base" % self.longname)

    def setup(self):
        self.aName = config.get("%s.instance" % self.longname, "last")

        instances = self.experiment.get_all_instance(self.base)
        if len(instances) == 0:
            raise Exception("Can not find any instance of experiment '%s'" % self.base)

        if self.aName == "last":
            self.aName, self.aDir = instances[-1]
        else:
            for n, d in instances:
                if self.aName == n:
                    self.aDir = d
                    break

    def run(self):
        self.bName = self.experiment.insname
        self.bDir = os.path.join(os.getcwd(), self.bName)

        # cwd = os.getcwd()
        # os.chdir(self.experiment.insname)
        self.run_script("%s.py" % self.name,
                        tauroot=self.experiment.tauroot,
                        aName=self.aName,
                        aDir=self.aDir,
                        bName=self.bName,
                        bDir=self.bDir,
                        metrics=self.metrics,
                        mode=self.mode,
                        throttle=self.throttle,
                        threshold=self.threshold,
                        taudb=self.experiment.datastore.config
                        )
        # os.chdir(cwd)
