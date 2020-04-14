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

    def setup_str(self) -> string:
        return ""

    def wrap_command(self, exe_cmd, exe_opt):
        datadir = self.experiment.datadirs[self.experiment.iteration]

        _execmd = "gprof"
        _execmd += " %s" % exe_cmd

        return [exe_cd, exe_opt]

    def aggregate(self):
        """
        Aggregate data collected by all iterations of the current
        experiment. We assume that iterations have all been finished.
        """
        # Not implemented yet
