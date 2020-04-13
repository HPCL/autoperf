class AbstractPlatform:
    name = "Abstract"

    def __init__(self, experiment):
        self.longname = "Platform.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

    def setup(self):
        raise NotImplementedError

    def setup_str(self):
        """
        Returns:
          string: A string of commands which should be executed before
                  any application which will run on this platform
        """
        raise NotImplementedError

    def build_env(self):
        """
        Returns:
          dict: A dict of environment variables which should be set
                before building any applications on this platform
        """
        raise NotImplementedError

    def run(self, execmd, exeopt, block=False):
        """
        Run an application on this platform.

        Args:
          execmd (string): the command going to run
          exeopt (string): the cmdline option for `exe_cmd`
          block  (bool)  : block until application exit?

        Returns:
          None
        """
        raise NotImplementedError

    def collect_data(self):
        """
        Collect the profiling data we get, do some postprocessing if
        necessary.

        Returns:
          None
        """
        raise NotImplementedError
