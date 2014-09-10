import os
import datetime
import subprocess
import shutil, shlex, errno
import ConfigParser

from partitioner import partitioner

from .utils import config

class Experiment:
    platform  = None
    tool      = None
    datastore = None
    analyses  = None

    def __init__(self, name, insname=None, mode="run"):
        experiments = config.get("Main.Experiments").split()
        if name not in experiments:
            raise Exception("Experiment '%s' not defined" % name)
        else:
            self.name     = name
            self.longname = "Experiments.%s" % name

        self.mode = mode

        if mode == "run":
            self.insname_fmt = datetime.datetime.now().isoformat() + "T%03d"
            print "*** Preparing to run %s" % self.name
        else:
            self.insname     = insname
            self.insname_fmt = None

        self.platform_name  = config.get("%s.Platform"   % self.longname, "generic")
        self.tool_name      = config.get("%s.Tool"       % self.longname, "tau")
        self.datastore_name = config.get("%s.Datastore"  % self.longname, "taudb")

        self.analyses_name  = config.get("%s.Analyses"   % self.longname).split()
        self.is_mpi         = config.getboolean("%s.mpi" % self.longname, False)
        self.tauroot        = config.get("%s.tauroot"    % self.longname)
        self.tauroot        = os.path.expanduser(self.tauroot)

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
        try:
            builder = config.get("%s.builder" % self.longname)
            builder = os.path.expanduser(builder)
        except ConfigParser.Error:
            return

        env = {
            'AP_ROOTDIR': self.rootdir,
            'AP_PLATFORM': self.platform_name,
            'AP_TOOL': self.tool_name,
            }

        env = dict(os.environ.items() + env.items())
        env = dict(env.items() + self.platform.build_env().items())

        process = subprocess.Popen(shlex.split(builder), env=env)

        returncode = process.wait()
        if returncode != 0:
            raise Exception("Builder failed")

    def setup(self):
        self.cwd     = os.getcwd()
        self.rootdir = config.get("%s.rootdir" % self.longname, self.cwd)
        self.rootdir = os.path.expanduser(self.rootdir)

        if not os.path.isdir(self.rootdir):
            os.makedirs(self.rootdir)

        os.chdir(self.rootdir)

        if self.mode == "run":
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

        # get all metrics we need to measure
        self.metrics = [ ]
        for analysis in self.analyses.values():
            self.metrics += analysis.metrics
        self.metrics = list(set(self.metrics))

        # partition the metrics
        dbfile = config.get("Partitioner.%s.dbfile" % self.name, "%s.db" % self.platform_name)
        algo   = config.get("Partitioner.%s.algo"   % self.name, "greedy")

        self.parted_metrics = partitioner(dbfile, self.metrics, algo, False)
        if len(self.parted_metrics) == 0:
            raise Exception("Metrics partition failed!")

    def run(self, block=False):
        execmd = config.get("%s.execmd" % self.longname)
        execmd = os.path.expanduser(execmd)
        exeopt = config.get("%s.exeopt" % self.longname, "")

        self.build()

        # run the experiment
        for i in range(len(self.parted_metrics)):
            self.insname = self.insname_fmt % i
            self.platform.run(execmd, exeopt, block)

    def check(self):
        return self.platform.check()

    def _analyze(self):
        for analysis in self.analyses.values():
            analysis.run()

    def analyze(self):
        # collect generated data and do the post-processing
        if self.insname_fmt is None:
            self.platform.collect_data()
            self._analyze()
        else:
            for i in range(len(self.parted_metrics)):
                self.insname = self.insname_fmt % i
                self.platform.collect_data()
                self._analyze()

    def cleanup(self):
        os.chdir(self.cwd)
