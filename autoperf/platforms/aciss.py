import os, sys
import signal, time, socket, tempfile, subprocess

from ..utils import config

class Platform:

    def __init__(self, experiment):
        self.done       = False
        self.name       = "aciss"
        self.longname   = "Platform.%s" % self.name
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
    
    def run(self, _execmd, _exeopt):
        execmd, exeopt = self.tool.wrap_command(_execmd, _exeopt)
        cmd = "%s %s" % (execmd, exeopt)
        
        if config.getboolean("%s.mpi" % self.experiment.longname):
            try:
                np = config.get("%s.mpi_np" % self.experiment.longname)
            except ConfigParser.Error:
                np = self.queue.numprocs;

            # see http://aciss-computing.uoregon.edu/2013/09/05/how-to-mpi/
            cmd = "mpirun --mca btl_tcp_if_include torbr -np %s %s" % (np, cmd)

        self.queue.submit(cmd)
        
    def collect_data(self):
        self.tool.collect_data()
        self.datastore.load()

    def analyze(self):
        self.tool.analyze()
