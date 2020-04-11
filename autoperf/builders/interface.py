class AbstractBuilder:
    name = "AbstractBuilder"

    def __init__(self, experiment):
        self.longname = "Builders.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment
        pass

    def setup(self):
        """
        Settings such as environment variables, modules to be loaded, etc. that must be
        done before attempting the build.

        Implementing this method in specific builders is optional
        Returns: nothing
        """
        return

    def configure(self, params=None):
        """
        Configure the external package prior to building (optional).
        Args:
            params: a dictionary of name = val pairs (all strings) with configuration parameters

        Returns: nothing
        """
        if params is None:
            params = {}
        return

    def build(self, params=None):
        """
        Build and optionally install the external package.

        Args:
            params: a dictionary of name = val pairs (all strings) with configuration parameters

        Returns: nothing
        """
        if params is None:
            params = {}
        raise NotImplementedError
