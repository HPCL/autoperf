import os
import logging
import ConfigParser

from .interface import AbstractPlatform
from ..utils import config

class Platform(AbstractPlatform):
    name     = "generic"
    mpi_opts = ""

    def __init__(self, experiment):
        self.longname   = "Platform.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        _queue  = config.get("%s.Queue" % self.longname, "serial")

        self.logger = logging.getLogger(__name__)
        self.logger.info("Queue    : %s", _queue)

        _module = __import__("queues.%s" % _queue, globals(), fromlist=["Queue"], level=2)
        self.queue = _module.Queue(self.experiment)

    def setup(self):
        self.tool      = self.experiment.tool
        self.datastore = self.experiment.datastore
        self.queue.setup()

    def setup_str(self):
        """
        Returns:
          string: A string of commands which should be executed before
                  any application which will run on this platform
        """
        prologue = "# Generic environment variables\n"
        for name, value in config.get_section("Env.%s" % self.experiment.name):
            prologue += "export %s='%s'\n" % (name, value)
        prologue += self.tool.setup_str()

        return prologue

    def build_env(self):
        """
        Returns:
          dict: A dict of environment variables which should be set
                before building any applications on this platform
        """
        env = { }

        env = dict(env.items() + self.tool.build_env().items())

        return env

    def run(self, _execmd, _exeopt, block=False):
        """
        Run an application on this platform.

        Args:
          execmd (string): the command going to run
          exeopt (string): the cmdline option for `execmd`
          block  (bool)  : block until application exit?

        Returns:
          None
        """
        execmd, exeopt = self.tool.wrap_command(_execmd, _exeopt)
        cmd = "%s %s" % (execmd, exeopt)

        if self.experiment.is_mpi:
            try:
                np = config.get("%s.mpi_np" % self.experiment.longname)
                np = "-np %s" % np
            except ConfigParser.Error:
                np = ""

            try:
                hostfile = config.get("%s.mpi_hostfile" % self.experiment.longname)
                hostfile = "--hostfile %s" % hostfile
            except ConfigParser.Error:
                hostfile = ""

            cmd = "mpirun %s %s %s %s" % (np, hostfile, self.mpi_opts, cmd)
        if self.experiment.threads > 1:
            cmd = "OMP_NUM_THREADS=%d %s" % (self.experiment.threads, cmd)

        self.logger.debug("Application command:")
        self.logger.debug("  Original: %s %s", _execmd, _exeopt)
        self.logger.debug("  ToolWrap: %s %s", execmd, exeopt)
        self.logger.debug("  Final   : %s", cmd)
        self.logger.debug("")

        self.queue.submit(cmd, block)

    def collect_data(self):
        """
        Collect the profiling data we get, do some postprocessing if
        necessary.

        Returns:
          None
        """
        if os.path.isfile("%s/data.ppk" % self.experiment.insname):
            self.logger.verb("Found data.ppk, bypassing data collection\n")
        else:
            self.tool.aggregate()
            self.tool.collect_data()
            self.datastore.load()
