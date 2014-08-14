import os
import subprocess
import ConfigParser

from ..utils import config

class Datastore:
    def __init__(self, experiment):
        self.name       = "taudb"
        self.longname   = "Datastore.taudb.%s" % experiment.name
        self.experiment = experiment

        self.config  = config.get("%s.config" % self.longname)

        try:
            self.appname = config.get("%s.appname" % self.longname)
        except ConfigParser.Error:
            self.appname = config.get("%s.execmd" % experiment.longname)
            self.appname = os.path.basename(self.appname)

    def setup(self):
        self.tool = self.experiment.tool

    def load(self):
        dispatch = {
            "tau":        self.load_tau,
            "hpctoolkit": self.load_hpctoolkit,
            }

        source = self.tool.name
        try:
            dispatch[source]()
        except KeyError as e:
            raise Exception("Invalid data source: %s" % e.args[0])

    def load_tau(self):
        subprocess.call(["perfdmf_loadtrial",
                         "-c",
                         self.config,
                         "-a",
                         self.appname,
                         "-x",
                         self.experiment.name,
                         "-n",
                         self.experiment.insname,
                         self.experiment.insname])

    def load_hpctoolkit(self):
        subprocess.call(["perfdmf_loadtrial",
                         "-c",
                         self.config,
                         "-f",
                         "hpc",
                         "-a",
                         self.appname,
                         "-x",
                         self.experiment.name,
                         "-n",
                         self.experiment.insname,
                         "%s/experiment.xml" % self.tool.database])
