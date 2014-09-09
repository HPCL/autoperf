import string
from ..utils import config

from .interface import AbstractAnalysis

class Analysis(AbstractAnalysis):

    def __init__(self, experiment):
        self.name       = "metrics"
        self.longname   = "Analyses.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        try:
            self.longmetrics = config.get("%s.metrics" % self.longname).split()
        except Exception:
            self.longmetrics = [ ]

        self.metrics = [m.partition('@')[0] for m in self.longmetrics]

        self.derived_metrics = dict()
        try:
            for name in config.get("%s.derived_metrics" % self.longname).split():
                self.derived_metrics[name] = config.get("%s.%s" % (self.longname, name))
                metrics = self.derived_metrics[name].translate(string.maketrans("()+-*/^", "       ")).split()
                for m in metrics:
                    try:
                        float(m)
                    except ValueError:
                        if m not in self.metrics:
                            self.metrics.append(m)
        except Exception:
            pass

    def run(self):
        self.run_script("%s.py" % self.name,
                        TAULIB          = "%s/lib" % self.experiment.tauroot,
                        ppk             = "%s.ppk" % self.experiment.insname,
                        derived_metrics = repr(self.derived_metrics)
                        )
