#!/usr/bin/env python

import os

from autoperf.utils      import config
from autoperf.experiment import *

experiment = Experiment("spA4_hpc")

experiment.setup()
experiment.run()
experiment.analyze()

