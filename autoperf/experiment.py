import os
import shutil, errno
import ConfigParser

from .utils import config

class Experiment:
    platform  = None
    tool      = None
    datastore = None
    analyses  = None

    def __init__(self, name):
        experiments = config.get("Main.Experiments").split()
        if name not in experiments:
            raise Exception("Experiment '%s' not defined" % name)
        else:
            self.name     = name
            self.longname = "Experiments.%s" % name

        self.platform_name  = config.get("%s.Platform" % self.longname)
        self.tool_name      = config.get("%s.Tool"     % self.longname)
        self.datastore_name = config.get("%s.Datastore" % self.longname)
        self.analyses_name  = config.get("%s.Analyses" % self.longname).split()

        _module = __import__("platforms.%s" % self.platform_name,
                             globals(),
                             fromlist=["Platform"],
                             level=1)
        self.platform = _module.Platform(self)

        _module = __import__("tools.%s" % self.tool_name,
                             globals(),
                             fromlist=["Tool"],
                             level=1)
        self.tool = _module.Tool(self)

        _module = __import__("datastores.%s" % self.datastore_name,
                             globals(),
                             fromlist=["Datastore"],
                             level=1)
        self.datastore = _module.Datastore(self)

        self.analyses = dict()
        for analysis in self.analyses_name:
            _module = __import__("analyses.%s" % analysis,
                                 globals(),
                                 fromlist=["Analysis"],
                                 level=1)
            self.analyses[analysis] = _module.Analysis(self)

    def build(self):
        pass

    def setup(self):
        cwd = os.path.expanduser(config.get("%s.rootdir" % self.longname))
        if not os.path.isdir(cwd):
            os.makedirs(cwd)
        os.chdir(cwd)

        # copy necessary files, if they are specified in config file
        try:
            for item in config.get("%s.copy" % self.longname).split():
                print "Copying %s ..." % item
                item = os.path.expanduser(item)
                try:
                    shutil.copytree(item, os.path.basename(item), True)
                except OSError as e:
                    if e.errno == errno.ENOTDIR:
                        shutil.copy(item, os.path.basename(item))
                    else:
                        raise
        except ConfigParser.Error:
            pass

        # link necessary files, if they are specified in config file
        try:
            for item in config.get("%s.link" % self.longname).split():
                print "Linking %s ..." % item
                item = os.path.expanduser(item)
                os.symlink(item, os.path.basename(item))
        except ConfigParser.Error:
            pass

        self.platform.setup()
        self.tool.setup()
        self.datastore.setup()

    def run(self, insname):
        execmd = config.get("%s.execmd" % self.longname)
        exeopt = config.get("%s.exeopt" % self.longname)

        execmd = os.path.expanduser(execmd)

        # set the name of this experiment instance
        self.insname = insname

        # run the experiment
        self.platform.run(execmd, exeopt)

        # collect generated data and do the post-processing
        self.platform.collect_data()

    def analyze(self):
        self.platform.analyze()
