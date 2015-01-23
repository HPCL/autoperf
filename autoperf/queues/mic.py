import os
import logging
import subprocess

from ..utils import config
from .interface import AbstractQueue

class Queue(AbstractQueue):
    mic_script = """#!/bin/sh
ulimit -s unlimited
export PATH={tau_root}/bin:$PATH
export LD_LIBRARY_PATH={ldlibpath}

cd {datadir}/../..

# mark the job as running
echo -n "{exp_name} {insname} mic Running" >{datadir}/.job.stat

# setup the environment for the experiment
{exp_setup}

# run the experiment
{exp_run} 2>&1 | tee {datadir}/job.log

# mark the job as finished
echo -n "{exp_name} {insname} mic Finished" >{datadir}/.job.stat
"""

    def __init__(self, experiment):
        self.name       = "mic"
        self.longname   = "Queue.%s.%s.%s" % (self.name, experiment.platform_name, experiment.name)
        self.experiment = experiment
        self.logger     = logging.getLogger(__name__)

        self.target = config.get("%s.target" % self.longname)

        self.nfsmaps    = dict()
        for m in config.get("%s.nfsmaps" % self.longname).split():
            a, b = m.split(":")
            self.nfsmaps[os.path.realpath(a)] = b;

        # rootdir and tauroot must be nfs mounted
        self.rootdir = self.host2mic(experiment.rootdir)
        self.tauroot = self.host2mic(experiment.tauroot)

        self.sinkpath  = config.get("%s.sinkpath" % self.longname, "/opt/intel/lib/mic")
        self.depends   = self.get_dependencies(experiment.execmd)
        self.ldlibpath = set()
        for d in self.depends:
            self.ldlibpath.add(os.path.dirname(d))
        self.ldlibpath = ":".join(map(self.host2mic, self.ldlibpath))


    def setup(self):
        self.platform = self.experiment.platform

    def host2mic(self, path):
        """
        Map a host path to mic path based on nfsmaps

        Args:
            path: a host path

        Return:
            string: mapped mic path

        Exception:
            cannot map the host path to mic path
        """
        path = os.path.expanduser(path)
        path = os.path.realpath(path)
        base = ""
        for m in self.nfsmaps:
            if path.startswith(m) and len(m) > len(base):
                base = m

        if len(base) == 0:
            raise Exception("`%s' is not maped to MIC, please check nfsmaps" % path)
        else:
            return path.replace(base, self.nfsmaps[base], 1)

    def get_dependencies(self, app):
        """
        Get the library dependencies of `app' with 'micnativeloadex -l'

        Args:
            app: the path of the application executable

        Return:
            list: a list of dependent library path
        """
        env = {'SINK_LD_LIBRARY_PATH': self.sinkpath}
        output = subprocess.check_output(["micnativeloadex", app, "-l"],
                                         env=dict(os.environ.items()+env.items()))
        depends = [ ]
        found = False;
        for line in map(str.strip, output.splitlines()):
            if line.startswith("Dependencies Found:"):
                found = True;
            elif line.startswith("Dependencies Not Found Locally"):
                break;
            else:
                if found and line != "" and line != "(none found)":
                    depends.append(line)

        return depends

    def get_status(self, idstr):
        queue, colon, pid = idstr.partition(":")
        if queue != "mic":
            print "queue: %s" % queue
            raise Exception("Fatal error: job queue mismatch!")

        # FIXME: need a way to know whether the job is killed or not
        return "Alive"

    def submit(self, cmd, block=False):
        datadir = self.experiment.datadirs[self.experiment.iteration]
        datadir = self.host2mic(datadir)
        jobstat = "%s/.job.stat" % datadir
        with open(jobstat, "w") as f:
            f.write("%s %s mic Queueing" % (self.experiment.name,
                                            self.experiment.insname))

        content = self.mic_script.format(
            tau_root  = self.tauroot,
            ldlibpath = self.ldlibpath,
            insname   = self.experiment.insname,
            exp_name  = self.experiment.name,
            exp_setup = self.platform.setup_str(),
            datadir   = datadir,
            exp_run   = cmd,
            )

        script_name = "%s/job.sh" % datadir

        self.logger.info("Populating the MIC native job script")
        with open(script_name, "w") as script:
            script.write(content)

        os.chmod(script_name, 0755)

        print "*** Submitting MIC native job ..."

        self.logger.info("Running the MIC native job script")
        self.logger.cmd("ssh %s %s\n", self.target, script_name)
        subprocess.call(["ssh", self.target, script_name])

    def wrap_command(self, execmd, exeopt):
        return [self.host2mic(execmd), exeopt]
