import os, sys
import signal, time, socket, tempfile, subprocess

from ..utils import config
from .interface import AbstractQueue

class Queue(AbstractQueue):

    pbs_script = """#!/bin/bash
#
#PBS -N autoperf.{hostname}.{pid}
#PBS -l nodes={pbs_nodes}:ppn={pbs_ppn}
#PBS -l walltime={pbs_walltime}
#PBS -l pmem={pbs_pmem}
#PBS -q {pbs_qname}
#PBS -j oe
#

cd $PBS_O_WORKDIR
NP=$(wc -l $PBS_NODEFILE | awk '{{print $1}}')

echo cwd: `pwd`
echo NP : $NP

# mark the job as running
echo -n PBS:$PBS_JOBID >running.{insname}

# setup the environment for the experiment
{exp_setup}

# run the experiment
{exp_run} 2>&1 | tee {insname}.log

# mark the job as finished
mv running.{insname} finished.{insname}

# notify autoperf that we are done
{notify}ssh {hostname} kill -SIGUSR1 {pid}
"""

    def __init__(self, experiment):
        self.name       = "PBS"
        self.longname   = "PBS.%s.%s" % (experiment.platform_name, experiment.name)
        self.experiment = experiment
        self.done       = False

        self.nodes     = config.get("%s.nodes"     % self.longname)
        self.ppn       = config.get("%s.ppn"       % self.longname)
        self.walltime  = config.get("%s.walltime"  % self.longname)
        self.pmem      = config.get("%s.pmem"      % self.longname)
        self.queuename = config.get("%s.queuename" % self.longname)

        self.numprocs = int(self.nodes) * int(self.ppn)

        signal.signal(signal.SIGUSR1, self._wakeup)

    def _wakeup(self, signum, frame):
        self.done = True

    def setup(self):
        self.platform = self.experiment.platform
        
    def submit(self, cmd, block=False):
        content = self.pbs_script.format(
            pbs_nodes    = self.nodes,
            pbs_ppn      = self.ppn,
            pbs_walltime = self.walltime,
            pbs_pmem     = self.pmem,
            pbs_qname    = self.queuename,
            exp_setup    = self.platform.setup_str(),
            exp_run      = cmd,
            pid          = os.getpid(),
            hostname     = socket.gethostname(),
            insname      = self.experiment.insname,
            notify       = "" if block else "# "
            )

        script = open("pbs_job.sh", "w+")
        script.write(content)
        script.flush()
        script.seek(0)

        print "*** Submitting batch task",

        # For Python 2.7+, we can use subprocess.check_output() instead
        process = subprocess.Popen("qsub",
                                   stdin=script,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()

        self.job_id = out.rstrip()

        print self.job_id + " " + self.experiment.insname + " ... done"

        script.close()

        if block:
            print "*** Waiting for the task to be finished...",
            sys.stdout.flush()

            while not self.done:
                time.sleep(10)
                sys.stdout.write('.')
                sys.stdout.flush()

            print " done"

            # reset the flag
            self.done = False

        return self.job_id

