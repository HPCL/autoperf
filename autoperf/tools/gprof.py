import logging
import os

from .interface import *


class Tool(AbstractTool):
    def __init__(self, experiment):
        self.name = "gprof"
        self.longname = "Tool.gprof.%s" % experiment.name
        self.experiment = experiment
        self.logger = logging.getLogger(__name__)

    def setup(self):
        self.platform = self.experiment.platform
        self.analyses = self.experiment.analyses

    def build_env(self):
        return dict()

    def setup_str(self) -> str:
        return ""

    def wrap_command(self, exe_cmd, exe_opt):
        datadir = self.experiment.datadirs[self.experiment.iteration]

        _execmd = " %s && %s %s gmon.out" % (exe_cmd, 'gprof', exe_cmd)

        return [_execmd, exe_opt]

    def aggregate(self):
        """
        Aggregate data collected by all iterations of the current
        experiment. We assume that iterations have all been finished.
        """
        # Not implemented yet
