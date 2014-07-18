import os

from .utils import config

class Experiment:
    platform = None
    tool     = None
    analyses = None

    def __init__(self, name):
        experiments = config.get("Main.Experiments").split()
        if name not in experiments:
            raise Exception("Experiment '%s' not defined" % name)
        else:
            self.name     = name
            self.longname = "Experiments.%s" % name

        self.platform_name = config.get("%s.Platform" % self.longname)
        self.tool_name     = config.get("%s.Tool"     % self.longname)
        self.analyses_name = config.get("%s.Analyses" % self.longname).split()

        _module = __import__("platforms.%s" % self.platform_name, globals(), fromlist=["Platform"], level=1)
        self.platform = _module.Platform(self)

        _module = __import__("tools.%s" % self.tool_name, globals(), fromlist=["Tool"], level=1)
        self.tool = _module.Tool(self)

        self.analyses = dict()
        for analysis in self.analyses_name:
            _module = __import__("analyses.%s" % analysis, globals(), fromlist=["Analysis"], level=1)
            self.analyses[analysis] = _module.Analysis(self)

    def build(self):
        pass

    def setup(self):
        cwd = os.path.expanduser(config.get("%s.rootdir" % self.longname))
        if not os.path.isdir(cwd):
            os.makedirs(cwd)
        os.chdir(cwd)

        self.platform.setup()
        self.tool.setup()

    def run(self):
        execmd = config.get("%s.execmd" % self.longname)
        exeopt = config.get("%s.exeopt" % self.longname)

        execmd = os.path.expanduser(execmd)

        self.platform.run(execmd, exeopt)
        self.platform.collect_data()

    def analyze(self):
        self.platform.analyze()
