class AbstractTool:
    name       = "Abstract"
    longname   = "Abstract"
    experiment = None

    def __init__(self, experiment):
        raise NotImplementedError

    def setup(self):
        raise NotImplementedError

    def build_env(self):
        """
        Returns:
          map: A map of environment variables which are need to build the
               app with the support of this tool
        """
        raise NotImplementedError

    def setup_str(self):
        """
        Returns:
          string: A string of commands which are needed to be executed
                  before running the app with the support of this tool
        """
        raise NotImplementedError

    def wrap_command(self, execmd, exeopt):
        """
        Args:
          execmd (string): the command used to run the app
          exeopt (string): the command line option for the app

        Returns:
          string: A string of command used to run `execmd exeopt` with the
                  support of this tool
        """
        raise NotImplementedError

    def collect_data(self):
        """
        Collect the profiling data and do some postprocessing if necessary

        Returns:
          None
        """
        raise NotImplementedError
