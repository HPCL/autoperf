import os, sys
import signal, time, socket, tempfile, subprocess
import ConfigParser

from ..utils import config
from .interface import AbstractQueue

class Queue(AbstractQueue):

    pbs_script = """#!/bin/bash
#
#PBS -N autoperf.{hostname}.{pid}
#PBS -o {insname}/pbs.log
#PBS -e {insname}/pbs.log
#PBS -j oe
#{pbs_nodes}
#{pbs_walltime}
#{pbs_pmem}
#{pbs_qname}
#

export PATH={tau_root}/bin:$PATH

cd $PBS_O_WORKDIR
NP=$(wc -l $PBS_NODEFILE | awk '{{print $1}}')

echo cwd: `pwd`
echo NP : $NP
echo PBS_NP: $PBS_NP

# mark the job as running
echo -n "{exp_name} {insname} PBS:$PBS_JOBID Running" >{insname}/job.stat

# setup the environment for the experiment
{exp_setup}

# run the experiment
{exp_run} 2>&1 | tee {insname}/job.log

# mark the job as finished
echo -n "{exp_name} {insname} PBS:$PBS_JOBID Finished" >{insname}/job.stat

# notify autoperf that we are done
{notify}ssh {hostname} kill -SIGUSR1 {pid}
"""

    def __init__(self, experiment):
        self.name       = "PBS"
        self.longname   = "Queue.%s.%s.%s" % (self.name, experiment.platform_name, experiment.name)
        self.experiment = experiment
        self.done       = False

        try:
            nodes = config.get("%s.nodes" % self.longname)
            try:
                ppn = config.get("%s.ppn" % self.longname)
                self.nodes = "PBS -l nodes=%s:ppn=%s" % (nodes, ppn)
            except ConfigParser.Error:
                self.nodes = "PBS -l nodes=%s" % nodes
        except ConfigParser.Error:
            self.nodes = ""

        try:
            walltime  = config.get("%s.walltime" % self.longname)
            self.walltime = "PBS -l walltime=%s" % walltime
        except ConfigParser.Error:
            self.walltime = ""

        try:
            pmem = config.get("%s.pmem" % self.longname)
            self.pmem = "PBS -l pmem=%s" % pmem
        except ConfigParser.Error:
            self.pmem = ""

        try:
            queuename = config.get("%s.queuename" % self.longname)
            self.queuename = "PBS -q %s" % queuename
        except:
            self.queuename = ""

        signal.signal(signal.SIGUSR1, self._wakeup)

    def _wakeup(self, signum, frame):
        self.done = True

    def setup(self):
        self.platform = self.experiment.platform
        
    def submit(self, cmd, block=False):
        content = self.pbs_script.format(
            tau_root     = self.experiment.tauroot,
            pbs_nodes    = self.nodes,
            pbs_walltime = self.walltime,
            pbs_pmem     = self.pmem,
            pbs_qname    = self.queuename,
            exp_name     = self.experiment.name,
            exp_setup    = self.platform.setup_str(),
            exp_run      = cmd,
            pid          = os.getpid(),
            hostname     = socket.gethostname(),
            insname      = self.experiment.insname,
            notify       = "" if block else "# "
            )

        script = open("%s/job.sh" % self.experiment.insname, "w+")
        script.write(content)
        script.flush()
        script.seek(0)

        print "*** Submitting PBS job",

        # For Python 2.7+, we can use subprocess.check_output() instead
        process = subprocess.Popen("qsub",
                                   stdin=script,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        out, err = process.communicate()

        self.job_id = out.rstrip()

        print "%s %s ... done" % (self.experiment.insname, self.job_id)

        script.close()

        f = open("%s/job.stat" % self.experiment.insname, "w+")
        f.write("%s %s PBS:%s Queueing" % (self.experiment.name,
                                           self.experiment.insname,
                                           self.job_id))
        f.close()

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

