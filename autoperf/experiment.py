import os
import logging
import datetime
import subprocess
import shutil, shlex, errno
import ConfigParser

from .             import logger as rootLogger
from .utils        import config
from .utils.logger import MyLogger

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

        self.timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        self.insname   = insname

        # get some basic config values
        self.platform_name  = config.get("%s.Platform"   % self.longname, "generic")
        self.tool_name      = config.get("%s.Tool"       % self.longname, "tau")
        self.datastore_name = config.get("%s.Datastore"  % self.longname, "taudb")
        self.analyses_name  = config.get("%s.Analyses"   % self.longname).split()

        self.cwd            = os.getcwd()
        self.rootdir        = config.get("%s.rootdir" % self.longname, self.cwd)
        self.rootdir        = os.path.expanduser(self.rootdir)
        self.rootdir        = os.path.join(self.cwd, self.rootdir)

        self.debug          = config.getboolean("%s.debug" % self.longname, True)
        self.is_mpi         = config.getboolean("%s.mpi"   % self.longname, False)
        self.is_cupti       = config.getboolean("%s.cupti" % self.longname, False)
        self.tauroot        = config.get("%s.tauroot"      % self.longname)
        self.tauroot        = os.path.expanduser(self.tauroot)

        # now let's get into the rootdir
        if not os.path.isdir(self.rootdir):
            os.makedirs(self.rootdir)
        os.chdir(self.rootdir)

        # init logger facility
        self.logger_init()

        # import submodules based on config options
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

        self.logger.info("");

    def logger_init(self):
        self.logger = logging.getLogger(__name__)

        # log destination
        logfile = config.get("Logger.%s.logfile" % self.name,
                             "%s/autoperf.log"   % self.rootdir)

        # log formatter
        # formatter = logging.Formatter(fmt="%(asctime)s %(levelname)-7s %(message)s",
        #                               datefmt="%m-%d-%y %H:%M:%S")
        formatter = logging.Formatter()

        # log handler
        self.logHandler = logging.FileHandler(logfile)
        self.logHandler.setFormatter(formatter)
        rootLogger.addHandler(self.logHandler)

        # log level
        loglvl = config.get("Logger.%s.loglvl" % self.name, "DEBUG")
        loglvl = getattr(logging, loglvl.upper(), None)
        if not isinstance(loglvl, int):
            loglvl = logging.DEBUG
            self.logger.log(logging.WARN, "# Invalid log level. Using default value (DEBUG)")

        rootLogger.setLevel(loglvl)

        self.logger.info("********** EXPERIMENT START **********")
        self.logger.info("")
        self.logger.info("Name     : %s", self.name)
        self.logger.info("Platform : %s", self.platform_name)
        self.logger.info("Tool     : %s", self.tool_name)
        self.logger.info("Analyses : %s", self.analyses_name)
        self.logger.info("Rootdir  : %s", self.rootdir)
        self.logger.info("MPI      : %s", self.is_mpi)
        self.logger.info("CUPTI    : %s", self.is_cupti)
        self.logger.info("Timestamp: %s", self.timestamp)
        self.logger.info("LogLevel : %s", logging.getLevelName(self.logger.getEffectiveLevel()))

    def build(self):
        """
        Run the builder command if it exist
        """
        try:
            builder = config.get("%s.builder" % self.longname)
            builder = os.path.expanduser(builder)
        except ConfigParser.Error:
            self.logger.verb("No builder found, bypass\n")
            return

        env = {
            'AP_ROOTDIR': self.rootdir,
            'AP_PLATFORM': self.platform_name,
            'AP_TOOL': self.tool_name,
            }

        env = dict(env.items() + self.platform.build_env().items())

        self.logger.info("Building the application")
        for key, val in env.items():
            self.logger.cmd("export %s='%s'", key, val)
        self.logger.cmd(builder)

        process = subprocess.Popen(shlex.split(builder),
                                   env=dict(os.environ.items()+env.items()))

        for key in env:
            self.logger.cmd("unset %s", key)
        self.logger.cmd("")

        returncode = process.wait()
        if returncode != 0:
            raise Exception("Builder failed")

    def setup(self):
        self.platform.setup()
        self.tool.setup()
        self.datastore.setup()

        for a in self.analyses:
            self.analyses[a].setup()

    def link_items(self):
        # link necessary files, if they are specified in config file
        try:
            items = config.get("%s.link" % self.longname).split()
        except ConfigParser.Error:
            self.logger.verb("Nothing to link, bypass\n")
            return

        self.logger.info("Linking necessary files")
        for item in items:
            print "Linking %s ..." % item
            item      = os.path.normpath(item)
            item      = os.path.expanduser(item)
            link_name = os.path.basename(item)
            if os.path.islink(link_name) and os.readlink(link_name) == item:
                # do nothing if the link is already there
                self.logger.verb("Link name is already there: %s", link_name)
            else:
                self.logger.cmd("ln -s %s %s", item, link_name)
                os.symlink(item, link_name)

    def copy_items(self):
        # copy necessary files, if they are specified in config file
        try:
            items = config.get("%s.copy" % self.longname).split()
        except ConfigParser.Error:
            self.logger.verb("Nothing to copy, bypass\n")
            return

        self.logger.info("Copying necessary files")
        for item in items:
            print "Copying %s ..." % item
            item = os.path.expanduser(item)
            self.logger.cmd("cp -r %s .", item)
            try:
                shutil.copytree(item, os.path.basename(item), True)
            except OSError as e:
                if e.errno == errno.ENOTDIR:
                    shutil.copy(item, os.path.basename(item))
                else:
                    self.logger.critical("CRITICAL: Something is wrong, abort\n")
                    self.cleanup()
                    raise

    def run(self, block=False):
        """
        Run the experiment.

        Args:
          block (bool): whether block until the experiment is finished

        Returns:
          None
        """
        print "*** Preparing to run %s" % self.name

        self.logger.info("Run the experiment")
        self.logger.cmd("function run-%s () {", self.timestamp)
        if self.logger.isEnabledFor(logging.CMD):
            self.logger.shift()
        self.logger.cmd("cd %s\n", self.rootdir)

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

        self.logger.info("Partitioning the metrics:")

        self.parted_metrics = partitioner(dbfile, self.metrics, algo, False)

        for i in range(len(self.parted_metrics)):
            self.logger.info("  %2d: %s", i+1, self.parted_metrics[i])

        if len(self.parted_metrics) == 0:
            self.logger.critical("CRITICAL: partitioner failed, abort\n")
            self.cleanup()
            raise Exception("Metrics partition failed!")

        # run the experiment
        for i in range(len(self.parted_metrics)):
            self.insname = self.timestamp + "T%03d" % i

            self.logger.info("Running experiment, pass %d/%d\n", i+1, len(self.parted_metrics))
            self.logger.cmd("mkdir -p %s", self.insname)

            os.makedirs(self.insname)
            self.platform.run(execmd, exeopt, block)

        self.insname = None

    def check(self):
        return self.platform.check()

    def analyze(self):
        self.logger.info("Analyze the experiment")

        if self.insname is None:
            self.logger.critical("CRITICAL: do not know the instanceId of the experiment, abort")
            raise Exception("Do not know the instanceId of the experiment")

        self.logger.cmd("function analyze-%s () {", self.insname)
        if self.logger.isEnabledFor(logging.CMD):
            self.logger.shift()
        self.logger.cmd("cd %s\n", self.rootdir)

        # collect generated data and do the post-processing
        self.platform.collect_data()

        # run the analyses
        self.logger.info("Running the analyses:")
        for analysis in self.analyses.values():
            analysis.run()

    def cleanup(self):
        self.logger.cmd("cd %s", self.cwd)

        os.chdir(self.cwd)

        if self.logger.isEnabledFor(logging.CMD):
            self.logger.unshift()
        self.logger.cmd( "}")
        self.logger.info("")
        self.logger.info("********** EXPERIMENT END   **********")

        # make sure there is a blank line for pretty print
        self.logger.log(logging.CRITICAL, "")

        rootLogger.removeHandler(self.logHandler)
