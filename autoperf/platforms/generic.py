import ConfigParser

from .interface import AbstractPlatform
from ..utils import config

class Platform(AbstractPlatform):
    name     = "generic"
    mpi_opts = ""

    def __init__(self, experiment):
        self.longname   = "Platform.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        _queue  = config.get("%s.Queue" % self.longname, "serial")
        _module = __import__("queues.%s" % _queue, globals(), fromlist=["Queue"], level=2)
        self.queue = _module.Queue(self.experiment)

    def setup(self):
        self.tool      = self.experiment.tool
        self.datastore = self.experiment.datastore
        self.queue.setup()

    def setup_str(self):
        return self.tool.setup_str()

    def build_env(self):
        env = { }

        env = dict(env.items() + self.tool.build_env().items())

        return env

    def run(self, _execmd, _exeopt, block=False):
        execmd, exeopt = self.tool.wrap_command(_execmd, _exeopt)
        cmd = "%s %s" % (execmd, exeopt)

        if self.experiment.is_mpi:
            try:
                np = config.get("%s.mpi_np" % self.experiment.longname)
                np = "-np %s" % np
            except ConfigParser.Error:
                np = ""

            try:
                hostfile = config.get("%s.mpi_hostfile" % self.experiment.longname)
                hostfile = "--hostfile %s" % hostfile
            except ConfigParser.Error:
                hostfile = ""

            cmd = "mpirun %s %s %s %s" % (np, hostfile, self.mpi_opts, cmd)

        self.queue.submit(cmd, block)

    def check(self):
        return self.queue.check()

    def collect_data(self):
        self.tool.collect_data()
        self.datastore.load()
