import os
import logging
import subprocess

from ..utils import config
from .interface import AbstractQueue

class Queue(AbstractQueue):
    serial_script = """#!/bin/sh
export PATH={tau_root}/bin:$PATH

# mark the job as running
echo -n "{exp_name} {insname} serial:$$ Running" >{datadir}/.job.stat

# setup the environment for the experiment
{exp_setup}

# run the experiment
{exp_run} 2>&1 | tee {datadir}/job.log

# mark the job as finished
echo -n "{exp_name} {insname} serial:$$ Finished" >{datadir}/.job.stat
"""

    def __init__(self, experiment):
        self.name       = "serial"
        self.experiment = experiment
        self.logger     = logging.getLogger(__name__)

    def setup(self):
        self.platform = self.experiment.platform

    def get_status(self, idstr):
        queue, colon, pid = idstr.partition(":")
        if queue != "serial":
            print "queue: %s" % queue
            raise Exception("Fatal error: job queue mismatch!")

        # sending signal 0 to a pid will raise OSError if the pid is
        # not running, and do nothing otherwise
        try:
            os.kill(int(pid), 0)
        except OSError:
            return "Dead"
        else:
            return "Alive"

    def submit(self, cmd, block=False):
        datadir = self.experiment.datadirs[self.experiment.iteration]
        jobstat = "%s/.job.stat" % datadir
        with open(jobstat, "w") as f:
            f.write("%s %s serial Queueing" % (self.experiment.name,
                                               self.experiment.insname))

        content = self.serial_script.format(
            tau_root  = self.experiment.tauroot,
            insname   = self.experiment.insname,
            exp_name  = self.experiment.name,
            exp_setup = self.platform.setup_str(),
            datadir   = datadir,
            exp_run   = cmd,
            )

        script_name = "%s/job.sh" % datadir

        self.logger.info("Populating the serial job script")
        with open(script_name, "w") as script:
            script.write(content)

        os.chmod(script_name, 0755)

        print "*** Submitting serial job ..."

        self.logger.info("Running the serial job script")
        self.logger.cmd("./%s\n", script_name)
        subprocess.call("./%s" % script_name)
