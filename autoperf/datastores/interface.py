class AbstractDatastore:
    name = "Abstract"

    def __init__(self, experiment):
        self.longname = "Analyses.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

    def setup(self):
        pass

    def load(self):
        """
        Load collected data to datastore
        """
        raise NotImplementedError
