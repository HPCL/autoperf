import os
import logging
import ConfigParser

from ..utils import config
from .interface import *

class Tool(AbstractTool):
    def __init__(self, experiment):
        self.name       = "tau"
        self.longname   = "Tool.tau.%s" % experiment.name
        self.experiment = experiment
        self.logger     = logging.getLogger(__name__)

    def setup(self):
        self.platform = self.experiment.platform
        self.analyses = self.experiment.analyses

        if self.experiment.is_mpi:
            self.binding = "mpi"
        else:
            self.binding = "serial"

        if self.experiment.is_cupti:
            self.binding += ",cupti"

    def get_tau_vars(self):
        """
        Get all TAU environment variables specified under [Tool.tau]

        Returns:
          map: A map from variable name to its value
        """
        tau_vars = dict()
        tau_options = config.get_section(self.longname)
        for name, value in tau_options:
            # take all upper case options as TAU environment variables
            if name.upper() == name:
                tau_vars[name] = value

        return tau_vars

    def build_env(self):
        """
        Returns:
          map: A map of environment variables needed to build
               application with TAU
        """
        env = self.get_tau_vars()
        env['TAU_ROOT'] = self.experiment.tauroot

        return env

    def setup_str(self):
        """
        Returns:
          string: A string of commands to be executed before running
                  TAU experiment
        """
        datadir   = self.experiment.datadirs[self.experiment.iteration]
        metrics   = self.experiment.parted_metrics[self.experiment.iteration]

        tau_setup = "# TAU environment variables\n"
        tau_vars  = self.get_tau_vars()
        for name in tau_vars:
            tau_setup += "export %s=%s\n" % (name, tau_vars[name])

        tau_setup += "export TAU_METRICS=%s\n" % metrics
        tau_setup += "export PROFILEDIR=%s/profiles\n" % datadir
        return tau_setup

    def wrap_command(self, execmd, exeopt):
        """
        Transmute application command line when necessary

        Returns:
          list: Transmuted application command
        """
        mode = config.get("%s.mode" % self.longname, "sampling")

        # do nothing for instrumented application
        if mode == "instrumentation":
            return [execmd, exeopt]

        # wrap the command with "tau_exec" for sampling
        if mode == "sampling":
            period = config.get("%s.period" % self.longname, 10000)
            source = config.get("%s.source" % self.longname, "TIME")

            tau_exec_opt  = "-T %s" % self.binding
            tau_exec_opt += " -ebs -ebs_period=%s -ebs_source=%s" % (period, source)
            if self.experiment.is_cupti:
                tau_exec_opt += " -cupti"
            tau_exec_opt += " %s" % execmd

            return ["tau_exec %s" % tau_exec_opt, exeopt]

        raise Exception("TAU: invalid mode: %s. (Available: instrumentation, sampling)" % mode)

    def aggregate(self):
        """
        Aggregate data collected by all iterations of the current
        experiment. We assume that iterations have all been finished.
        """
        self.logger.info("Aggregating all collected data")

        for datadir in self.experiment.datadirs:
            metrics = os.listdir("%s/profiles" % datadir)
            for metric in metrics:
                target    = os.path.relpath("%s/profiles/%s" % (datadir, metric),
                                            "%s/profiles"    % self.experiment.insname)
                link_name = "%s/profiles/%s" % (self.experiment.insname, metric)

                self.logger.cmd("ln -s %s %s", target, link_name)

                # link error will happen if different iterations share
                # some metrics, in this case we just ignore the error
                try:
                    os.symlink(target, link_name)
                except:
                    pass

        self.logger.newline()
