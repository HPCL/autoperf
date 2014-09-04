class AbstractPlatform:
    name       = "Abstract"
    longname   = "Abstract"
    experiment = None

    def __init__(self, experiment):
        raise NotImplementedError

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
          exeopt (string): the cmdline option for `execmd`
          block  (bool)  : block until application exit?

        Returns:
          None
        """
        raise NotImplementedError

    def check(self):
        """
        Check the status of the applications running on this platform

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
