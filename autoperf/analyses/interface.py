from ..utils import script


class AbstractAnalysis:
    name = "Abstract"

    def __init__(self, experiment):
        self.longname = "Analyses.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        # metrics needed for this analysis
        self.metrics = []

        # metric names with possible annotation, e.g. "for hpcrun -e"
        self.longmetrics = []

    def setup(self):
        pass

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
