from ..utils import config

from .interface import AbstractAnalysis

class Analysis(AbstractAnalysis):

    def __init__(self, experiment):
        self.name        = "gensel"
        self.longname    = "Analyses.%s.%s" % (self.name, experiment.name)
        self.experiment  = experiment
        self.metrics     = ['TIME']
        self.longmetrics = ['TIME']

        self.rule       = config.get("%s.rule" % self.longname)
        self.selfile    = config.get("%s.selfile" % self.longname)

    def run(self):
        self.run_script("%s.sh" % self.name,
                        insname = self.experiment.insname,
                        selfile = self.selfile,
                        )
