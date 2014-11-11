import logging
from .interface import AbstractDatastore

class Datastore(AbstractDatastore):
    def __init__(self, experiment):
        self.name   = "nop"
        self.logger = logging.getLogger(__name__)
        AbstractDatastore.__init__(self, experiment)

    def load(self):
        # do nothing
        self.logger.info("Datastore not specified, bypass loading")
