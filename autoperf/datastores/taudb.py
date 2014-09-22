import os
import ConfigParser

from ..utils import config
from ..utils import script

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
        script.run("taudb_loadtrial.py", None,
                   tauroot  = self.experiment.tauroot,
                   taudb    = self.config,
                   filetype = "profiles",
                   appname  = self.appname,
                   expname  = self.experiment.name,
                   trial    = self.experiment.insname,
                   source   = "profiles")

    def load_hpctoolkit(self):
        script.run("taudb_loadtrial.py", None,
                   tauroot  = self.experiment.tauroot,
                   taudb    = self.config,
                   filetype = "hpc",
                   appname  = self.appname,
                   expname  = self.experiment.name,
                   trial    = self.experiment.insname,
                   source   = "database/experiment.xml")
