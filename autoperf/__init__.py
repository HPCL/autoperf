import os
from .utils import config

# parse the config file
config.parse(['.autoperf.cfg', 'autoperf.cfg',
              os.path.expanduser('~/.autoperf.cfg')])
