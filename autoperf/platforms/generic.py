import os
from importlib import import_module

from .interface import AbstractPlatform
from ..utils import config


class Platform(AbstractPlatform):
    name = "generic"
    launcher = ""
    launcher_opts = ""

    def __init__(self, experiment):
        self.longname = "Platform.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        if self.launcher == "":
            self.launcher = self.experiment.config.get("%s.launcher" % experiment.longname, "")

        self.launcher_opts += self.experiment.config.get("%s.launcher_opts" % experiment.longname, "")

        _queue = self.experiment.config.get("%s.Queue" % self.longname, "serial")

        self.logger = self.experiment.logger
        self.logger.info("Queue    : %s", _queue)

        _module = import_module(".%s" % _queue, package="autoperf.queues")
        self.queue = _module.Queue(self.experiment)

    def setup(self):
        self.tool = self.experiment.tool
        self.datastore = self.experiment.datastore
        self.queue.setup()

    def setup_str(self):
        """
        Returns:
          string: A string of commands which should be executed before
                  any application which will run on this platform
        """
        prologue = "# Generic environment variables\n"
        for name, value in self.experiment.config.get_section("Env.%s" % self.experiment.name):
            prologue += "export %s='%s'\n" % (name, value)

        # print "NUMBER OF THREADS = %d" % self.experiment.threads
        prologue += "export OMP_NUM_THREADS=%d\n" % (self.experiment.threads)
        prologue += self.tool.setup_str()

        return prologue

    def build_env(self):
        """
        Returns:
          dict: A dict of environment variables which should be set
                before building any applications on this platform
        """
        env = {}

        env = dict(list(env.items()) + list(self.tool.build_env().items()))

        return env

    def wrap_command(self, _execmd, _exeopt):
        exe_cmd, exe_opts = self.queue.wrap_command(_execmd, _exeopt)
        exe_cmd, exe_opts = self.tool.wrap_command(exe_cmd, exe_opts)

        # ignore launcher and launcher option if they are not specified
        if self.launcher == "":
            cmd = "%s %s" % (exe_cmd, exe_opts)
        else:
            cmd = "%s %s %s %s" % (self.launcher, self.launcher_opts, exe_cmd, exe_opts)

        cmd = cmd.strip()

        if self.experiment.threads > 1:
            cmd = "OMP_NUM_THREADS=%d %s" % (self.experiment.threads, cmd)

        self.logger.debug("Application command:")
        self.logger.debug("  Original: %s %s", _execmd, _exeopt)
        self.logger.debug("  ToolWrap: %s %s", exe_cmd, exe_opts)

        return cmd

    def run(self, _execmd, _exeopt, block=False):
        """
        Run an application on this platform.

        Args:
          _execmd (string): the command going to run
          _exeopt (string): the cmdline option for `_execmd`
          block  (bool)  : block until application exit?

        Returns:
          None
        """
        cmd = self.wrap_command(_execmd, _exeopt)
        self.logger.debug("  Final   : %s", cmd)
        self.queue.submit(cmd, block)

    def collect_data(self):
        """
        Collect the profiling data we get, do some postprocessing if
        necessary.

        Returns:
          None
        """
        if os.path.isfile("%s/%s.ppk" % (self.experiment.insname, self.experiment.ppkname)):
            self.logger.verb("Found ppk file, bypassing data collection\n")
        else:
            self.tool.aggregate()
            self.tool.collect_data()
            self.datastore.load()
