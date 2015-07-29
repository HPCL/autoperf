import subprocess

from ..utils import config
from ..utils.PPK import PPK

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

        if (num > 0):
            ppk.dump(ppkfile)
