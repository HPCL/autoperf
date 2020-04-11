import pytest
from ..autoperf.utils.config import Config

def load_default_config(): 
    config = Config()
    config.parse()
    return config


def test_config_default():
    cfg = load_default_config()
    assert cfg != None
    assert cfg.get('Experiments.rootdir','default') == "performance-results"

