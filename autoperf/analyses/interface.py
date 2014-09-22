import os, subprocess

from ..utils import script

class AbstractAnalysis:
    name        = "Abstract"
    longname    = "Abstract"
    experiment  = None

    # metrics needed for this analysis
    metrics     = [ ]

    # metric names with possible annotation, e.g. "for hpcrun -e"
    longmetrics = [ ]

    def __init__(self, experiment):
        raise NotImplementedError

    def run(self):
        """
        Run this analysis
        """
        raise NotImplementedError

    def run_script(self, template, **kwargs):
        if self.experiment.debug:
            script_name = "%s/%s" % (self.experiment.insname, template)
        else:
            script_name = None

        script.run(template, script_name, **kwargs)
