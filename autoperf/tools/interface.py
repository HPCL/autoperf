import subprocess

from ..utils import config
from ..utils.PPK import PPK


class AbstractTool:
    name = "Abstract"
    longname = "Abstract"
    experiment = None

    def __init__(self, experiment):
        raise NotImplementedError

    def setup(self):
        """
        Perform necessary tool setup.
        Returns:
          Nothing
        """
        raise NotImplementedError

    def build_env(self) -> dict:
        """
        Returns:
          map: A dictionary of environment variables which are need to build the
               app with the support of this tool
        """
        raise NotImplementedError

    def setup_str(self) -> str:
        """
        Returns:
          string: A string of commands which are needed to be executed
                  before running the app with the support of this tool
        """
        raise NotImplementedError

    def wrap_command(self, exe_cmd, exe_opt) -> (str,str):
        """
        Args:
          exe_cmd (string): the command used to run the app
          exe_opt (string): the command line option for the app

        Returns:
          string: A pair of strings containing the command used to run `execmd exe_opt` with the
                  support of this tool
        """
        raise NotImplementedError

    def collect_data(self):
        """
        Collect the profiling data and do some postprocessing if necessary

        Returns:
          Nothing
        """
        ppkfile = "%s/%s.ppk" % (self.experiment.insname, self.experiment.ppkname)
        cmd = ["%s/bin/paraprof" % self.experiment.tauroot,
               "--pack",
               ppkfile,
               "%s/profiles" % self.experiment.insname]
        self.logger.info("Pack collected data to TAU .ppk package")
        self.logger.cmd(' '.join(cmd))
        process = subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()

        # now add user specified metadata
        num = 0
        ppk = PPK(ppkfile, "");
        for name, value in config.get_section("Metadata.%s" % self.experiment.name):
            num += 1
            ppk.addMetadata(name, value)

        # also calculate and attach derived metrics
        metric_set = self.experiment.metric_set
        if metric_set.dmetrics:
            num += len(metric_set.dmetrics)
            ppk.attachMetricSet(metric_set)

        if (num > 0):
            ppk.dump(ppkfile)
