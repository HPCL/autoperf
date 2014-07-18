import string
from ..utils import config

class Parser:
    """
    Lexing and parsing an arithmetic expression.
    """

    tokens = [ ]

    def __init__(self, expression):
        self.lex(expression)

    def lex(self, expression):
        pass

class Analysis:

    def __init__(self, experiment):
        self.name       = "metrics"
        self.longname   = "Analyses.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        try:
            self.metrics = config.get("%s.metrics" % self.longname).split()
        except Exception:
            self.metrics = [ ]

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
