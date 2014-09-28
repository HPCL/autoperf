import os
import logging
import subprocess
import ConfigParser

from ..utils import config
from .interface  import *

class Tool(AbstractTool):
    def __init__(self, experiment):
        self.name        = "hpctoolkit"
        self.longname    = "Tool.hpctoolkit.%s" % experiment.name
        self.experiment  = experiment
        self.logger      = logging.getLogger(__name__)

    def setup(self):
        self.platform = self.experiment.platform
        self.analyses = self.experiment.analyses

        self.metrics = [ ]
        for analysis in self.analyses.values():
            self.metrics += analysis.longmetrics

    def build_env(self):
        return dict()

    def setup_str(self):
        return ""

    def wrap_command(self, execmd, exeopt):
        datadir = self.experiment.datadirs[self.experiment.iteration]
        metrics = self.experiment.parted_metrics[self.experiment.iteration]

        measurement = "%s/measurement" % datadir
        _execmd = "hpcrun -o %s" % measurement

        # FIXME: event period is missing
        for metric in metrics.split(':'):
            _execmd += " -e %s" % metric

        _execmd += " %s" % execmd

        return [_execmd, exeopt]

    def aggregate(self):
        """
        Aggregate data collected by all iterations of the current
        experiment. We assume that iterations have all been finished.
        """
        execmd = config.get("%s.execmd" % self.experiment.longname)
        execmd = os.path.expanduser(execmd)
        exebin = os.path.basename(execmd)
        appsrc = config.get("%s.appsrc" % self.longname)

        self.logger.info("Aggregating all collected data")
        hpcstruct = "%s/%s.hpcstruct" % (self.experiment.insname, exebin)
        cmd = ["hpcstruct",
               "-o",
               hpcstruct,
               execmd]
        self.logger.info("HPCToolkit: run hpcstruct")
        self.logger.cmd(' '.join(cmd))
        subprocess.call(cmd)

        # This could be stupid, but it is the only way I know to
        # aggregate HPCToolkit collected data:
        for datadir in self.experiment.datadirs:
            measurement = "%s/measurement" % datadir
            database    = "%s/database"    % datadir

            # 1. convert to ppk (paraprof -f hpc --pack)
            cmd =["hpcprof",
                  "-o",
                  database,
                  "-S",
                  hpcstruct,
                  "-I",
                  "%s/'*'" % appsrc,
                  measurement]
            self.logger.info("HPCToolkit: run hpcprof")
            self.logger.cmd(' '.join(cmd))
            subprocess.call(cmd)

            cmd = ["%s/bin/paraprof" % self.experiment.tauroot,
                   "-f",
                   "hpc",
                   "--pack",
                   "%s/data.ppk" % datadir,
                   "%s/experiment.xml" % database]
            self.logger.info("Pack collected data to TAU .ppk package")
            self.logger.cmd(' '.join(cmd))
            process = subprocess.Popen(cmd,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            out, err = process.communicate()

            # 2. dump as tau profile (paraprof --dump)
            cwd = os.getcwd()
            self.logger.cmd("cd %s/profiles", datadir)
            os.chdir("%s/profiles" % datadir)

            cmd = ["%s/bin/paraprof" % self.experiment.tauroot,
                   "--dump",
                   "../data.ppk"]
            self.logger.info("Unpack .ppk to TAU profiles")
            self.logger.cmd(' '.join(cmd))
            process = subprocess.Popen(cmd,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            out, err = process.communicate()

            self.logger.cmd("cd %s", cwd)
            os.chdir(cwd)

            # 3. aggregate tau profiles
            for metric in os.listdir("%s/profiles" % datadir):
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
