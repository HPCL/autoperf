import logging
import os
from glob import glob

from .interface import *


class Tool(AbstractTool):
    def __init__(self, experiment):
        self.name = "tau"
        self.longname = "Tool.tau.%s" % experiment.name
        self.experiment = experiment
        self.logger = logging.getLogger(__name__)

    def setup(self):
        self.platform = self.experiment.platform
        self.analyses = self.experiment.analyses

        options = self.get_tau_bindings()

        if not 'mpi' in options:
            self.binding = "serial"  # default, should always work

        # self.binding = "papi,pdt"
        # options = [b for b in options if 'papi' in b]
        # options = [b for b in options if 'pdt' in b]

        if self.experiment.is_cupti:
            self.binding += ",cupti"
            options = [b for b in options if 'cupti' in b]

        if self.experiment.is_mpi:
            self.binding += ",mpi"
            options = [b for b in options if 'mpi' in b]
        else:
            self.binding += ",serial"
            options = [b for b in options if 'mpi' not in b]

        if len(options) == 0:
            raise Exception("Error: TAU is not configured to support binding `%s'" % self.binding);

        # enable pthread tracking whenever possible
        options = [b for b in options if 'pthread' in b];
        if len(options) > 0:
            self.binding += ",pthread"

        self.logger.info("Using TAU binding: %s" % self.binding)

    def get_tau_bindings(self):
        """ Get available TAU bindings combination """
        makefiles = list(map(os.path.basename, glob("%s/lib/Makefile.tau-*" % self.experiment.tauroot)))
        if makefiles:
            return [str.split(s, '-')[1:] for s in makefiles]
        else:
            return []

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
        datadir = self.experiment.datadirs[self.experiment.iteration]
        metrics = self.experiment.parted_metrics[self.experiment.iteration]

        # make sure more than one metrics are measured, so TAU will
        # put data into MULTI__* directory, so we can easily aggregate
        # them together
        if len(metrics.split(':')) == 1:
            metrics = "%s:TIME" % metrics

        tau_setup = "# TAU environment variables\n"
        tau_vars = self.get_tau_vars()
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

            tau_exec_opt = "-T %s" % self.binding
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
                target = os.path.relpath("%s/profiles/%s" % (datadir, metric),
                                         "%s/profiles" % self.experiment.insname)
                link_name = "%s/profiles/%s" % (self.experiment.insname, metric)

                self.logger.cmd("ln -s %s %s", target, link_name)

                # link error will happen if different iterations share
                # some metrics, in this case we just ignore the error
                try:
                    os.symlink(target, link_name)
                except:
                    pass

        self.logger.newline()
