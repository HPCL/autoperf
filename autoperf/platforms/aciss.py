import os, sys
import signal, time, socket, tempfile, subprocess
import ConfigParser

from ..utils import config

class Platform:

    def __init__(self, experiment):
        self.done       = False
        self.name       = "aciss"
        self.longname   = "Platform.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        _queue  = config.get("%s.Queue" % self.longname)
        _module = __import__("queues.%s" % _queue, globals(), fromlist=["Queue"], level=2)
        self.queue = _module.Queue(experiment)

    def setup_str(self):
        return self.tool.setup_str()

    def setup(self):
        self.tool      = self.experiment.tool
        self.datastore = self.experiment.datastore
        self.queue.setup()

    def build_env(self):
        env = { }

        env = dict(env.items() + self.tool.build_env().items())

        return env
    
    def run(self, _execmd, _exeopt, block=False):
        execmd, exeopt = self.tool.wrap_command(_execmd, _exeopt)
        cmd = "%s %s" % (execmd, exeopt)
        
        if config.getboolean("%s.mpi" % self.experiment.longname):
            try:
                np = config.get("%s.mpi_np" % self.experiment.longname)
            except ConfigParser.Error:
                np = self.queue.numprocs;

            try:
                hostfile = config.get("%s.mpi_hostfile" % self.experiment.longname)
                hostfile = "--hostfile %s" % hostfile
            except ConfigParser.Error:
                hostfile = ""

            # see http://aciss-computing.uoregon.edu/2013/09/05/how-to-mpi/
            cmd = "mpirun --mca btl_tcp_if_include torbr -np %s %s %s" % (np, hostfile, cmd)

        self.queue.submit(cmd, block)

    def check(self):
        return self.queue.check()
        
    def collect_data(self):
        self.tool.collect_data()
        self.datastore.load()
