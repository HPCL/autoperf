import os
import datetime
import subprocess
import shutil, shlex, errno
import ConfigParser

from .utils import config

class Experiment:
    platform  = None
    tool      = None
    datastore = None
    analyses  = None

    def __init__(self, name, insname=None):
        experiments = config.get("Main.Experiments").split()
        if name not in experiments:
            raise Exception("Experiment '%s' not defined" % name)
        else:
            self.name     = name
            self.longname = "Experiments.%s" % name

        self.timestamp = datetime.datetime.now().isoformat()
        self.insname   = insname

        self.platform_name  = config.get("%s.Platform"   % self.longname, "generic")
        self.tool_name      = config.get("%s.Tool"       % self.longname, "tau")
        self.datastore_name = config.get("%s.Datastore"  % self.longname, "taudb")
        self.analyses_name  = config.get("%s.Analyses"   % self.longname).split()

        self.debug          = config.getboolean("%s.debug" % self.longname, True)
        self.is_mpi         = config.getboolean("%s.mpi"   % self.longname, False)
        self.is_cupti       = config.getboolean("%s.cupti" % self.longname, False)
        self.tauroot        = config.get("%s.tauroot"      % self.longname)
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
        """
        Run the builder command if it exist
        """
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

        self.platform.setup()
        self.tool.setup()
        self.datastore.setup()

        for a in self.analyses:
            self.analyses[a].setup()

    def link_items(self):
        # link necessary files, if they are specified in config file
        try:
            for item in config.get("%s.link" % self.longname).split():
                print "Linking %s ..." % item
                item      = os.path.normpath(item)
                item      = os.path.expanduser(item)
                link_name = os.path.basename(item)
                if os.path.islink(link_name) and os.readlink(link_name) == item:
                    # do nothing if the link is already there
                    pass
                else:
                    os.symlink(item, link_name)
        except ConfigParser.Error:
            pass

    def copy_items(self):
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


    def run(self, block=False):
        """
        Run the experiment.

        Args:
          block (bool): whether block until the experiment is finished

        Returns:
          None
        """
        print "*** Preparing to run %s" % self.name

        execmd = config.get("%s.execmd" % self.longname)
        execmd = os.path.expanduser(execmd)
        exeopt = config.get("%s.exeopt" % self.longname, "")

        self.link_items()
        self.copy_items()
        self.build()

        # get all metrics we need to measure
        self.metrics = [ ]
        for analysis in self.analyses.values():
            self.metrics += analysis.metrics
        self.metrics = list(set(self.metrics))

        # partition the metrics
        dbfile = config.get("Partitioner.%s.dbfile" % self.name, "%s.db" % self.platform_name)
        algo   = config.get("Partitioner.%s.algo"   % self.name, "greedy")

        from partitioner import partitioner
        self.parted_metrics = partitioner(dbfile, self.metrics, algo, False)
        if len(self.parted_metrics) == 0:
            raise Exception("Metrics partition failed!")

        # run the experiment
        for i in range(len(self.parted_metrics)):
            self.insname = self.timestamp + "T%03d" % i
            os.makedirs(self.insname)
            self.platform.run(execmd, exeopt, block)

        self.insname = None

    def check(self):
        return self.platform.check()

    def _analyze(self):
        for analysis in self.analyses.values():
            analysis.run()

    def analyze(self):
        # collect generated data and do the post-processing
        if self.insname is None:
            for i in range(len(self.parted_metrics)):
                self.insname = self.timestamp + "T%03d" % i
                self.platform.collect_data()
                self._analyze()
        else:
            self.platform.collect_data()
            self._analyze()

    def cleanup(self):
        os.chdir(self.cwd)
