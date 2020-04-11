import configparser
import logging
import os

from .interface import AbstractDatastore
from ..utils import config
from ..utils import script


class Datastore(AbstractDatastore):
    def __init__(self, experiment):
        super().__init__(experiment)

        self.name = "taudb"
        self.longname = "Datastore.taudb.%s" % experiment.name
        self.experiment = experiment
        self.tool = self.experiment.tool
        self.logger = logging.getLogger(__name__)

        self.config = config.get("%s.config" % self.longname)

        try:
            self.appname = config.get("%s.appname" % self.longname)
        except configparser.Error:
            self.appname = config.get("%s.execmd" % experiment.longname)
            self.appname = os.path.basename(self.appname)

    def setup(self):
        pass

    def load(self):
        self.logger.info("Loading collected data to TAUdb:")

        script.run("taudb_loadtrial.py",
                   "%s/taudb_loadtrial.py" % self.experiment.insname,
                   tauroot=self.experiment.tauroot,
                   taudb=self.config,
                   filetype="packed",
                   appname=self.appname,
                   expname=self.experiment.name,
                   trial=self.experiment.insname,
                   source="data.ppk")
