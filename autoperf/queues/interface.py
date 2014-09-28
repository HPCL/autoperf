import os
import re

class AbstractQueue:
    name       = "Abstract"
    longname   = "Abstract"
    experiment = None

    def __init__(self, experiment):
        raise NotImplementedError

    def setup(self):
        raise NotImplementedError

    def submit(self, cmd, block=False):
        raise NotImplementedError
