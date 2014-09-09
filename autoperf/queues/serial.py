import os
import subprocess

from ..utils import config
from .interface import AbstractQueue

class Queue(AbstractQueue):
    serial_script = """#!/bin/sh
export PATH={tau_root}/bin:$PATH

# mark the job as running
echo -n {exp_name}:serial >running.{insname}

# setup the environment for the experiment
{exp_setup}

# run the experiment
{exp_run}

# mark the job as finished
mv running.{insname} finished.{insname}
"""

    def __init__(self, experiment):
        self.name = "serial"
        self.experiment = experiment

    def setup(self):
        self.platform = self.experiment.platform

    def submit(self, cmd, block=False):
        content = self.serial_script.format(
            tau_root  = self.experiment.tauroot,
            insname   = self.experiment.insname,
            exp_name  = self.experiment.name,
            exp_setup = self.platform.setup_str(),
            exp_run   = cmd,
            )

        script_name = "%s.serial_job.sh" % self.experiment.insname
        script = open(script_name, "w+")
        script.write(content)
        script.close()
        os.chmod(script_name, 0755)

        print "*** Submitting serial task ..."

        subprocess.call("./%s" % script_name)
