from setuptools import setup, find_packages

setup(
    name             = "autoperf",
    version          = "0.1.0",
    author           = "Ender Dai",
    author_email     = "xdai@uoregon.edu",
    packages         = find_packages(),
    scripts          = ["bin/perf.py"],
    license          = "BSD",
    description      = "Automation for experiment, perf and analysis",
    )
