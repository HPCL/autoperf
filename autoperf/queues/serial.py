import os
import subprocess

from ..utils import config
from .interface import AbstractQueue

class Queue(AbstractQueue):
    serial_script = """#!/bin/sh
export PATH={tau_root}/bin:$PATH

# mark the job as running
echo -n "{exp_name} {insname} serial Running" >{insname}/job.stat

# setup the environment for the experiment
{exp_setup}

# run the experiment
{exp_run} 2>&1 | tee {insname}/job.log

# mark the job as finished
echo -n "{exp_name} {insname} serial Finished" >{insname}/job.stat
"""

    def __init__(self, experiment):
        self.name = "serial"
        self.experiment = experiment

    def setup(self):
        self.platform = self.experiment.platform

    def submit(self, cmd, block=False):
        f = open("%s/job.stat" % self.experiment.insname, "w+")
        f.write("%s %s serial Queueing" % (self.experiment.name,
                                           self.experiment.insname))
        f.close()

        content = self.serial_script.format(
            tau_root  = self.experiment.tauroot,
            insname   = self.experiment.insname,
            exp_name  = self.experiment.name,
            exp_setup = self.platform.setup_str(),
            exp_run   = cmd,
            )

        script_name = "%s/job.sh" % self.experiment.insname
        script = open(script_name, "w+")
        script.write(content)
        script.close()
        os.chmod(script_name, 0755)

        print "*** Submitting serial job ..."

        subprocess.call("./%s" % script_name)
