import configparser
import datetime
import errno
import logging
import os
import re
import shlex
import shutil
import subprocess
from importlib import import_module

from .utils import logger
from .utils.MetricSet import MetricSet
from .utils.config import Config
from .utils.portability import fix_path
from .platforms import generic


class Experiment:
    """
    Performance experiment definition. The minimal configuration is using TAU,
    which will be built on demand, with just time as the metric and local
    datastore.
    """

    def __init__(self, config: Config, name, insname=''):
        """
        Instantiating an experiment. Do the first step of the
        initialization. If `insname` is not given, it will take
        current timestamp as the default value.

        Args:
          name    (string): The name of this experiment
          insname (string): The instance ID of this experiment
        """

        # Defaults:
        self.platform = generic.Platform
        self.logHandler = None

        # Configuration options
        self.config = config

        experiments = self.config.get_list("Main.Experiments")
        if name not in experiments:
            raise Exception("Unknown experiment: '%s'" % name)
        else:
            self.name = name
            self.longname = "Experiments.%s" % name

        self.datadirs = []

        # get some basic config values
        self.platform_name = self.config.get("%s.Platform" % self.longname, default="generic").split(';')[0].rstrip()
        self.tool_name = self.config.get("%s.Tool" % self.longname, default="gprof").split(';')[0].rstrip()
        self.datastore_name = self.config.get("%s.Datastore" % self.longname, default="nop").split(';')[0].rstrip()
        self.analyses_names = [x.rstrip() for x in self.config.get("%s.Analyses" % self.longname, default='').split()]

        self.cwd = os.getcwd()
        self.rootdir = self.config.get("%s.rootdir" % self.longname, self.cwd)
        self.rootdir = os.path.expanduser(self.rootdir)
        self.rootdir = os.path.join(self.cwd, self.rootdir)
        try:
            os.stat(self.rootdir)
        except:
            os.mkdir(self.rootdir)

        if not insname:
            self.insname = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")
        else:
            self.insname = insname

        self.debug = self.config.getboolean("%s.debug" % self.longname, True)
        self.is_mpi = self.config.getboolean("%s.mpi" % self.longname, False)
        self.is_cupti = self.config.getboolean("%s.cupti" % self.longname, False)
        try:
            self.tauroot = self.config.get("%s.tauroot" % self.longname)
            self.tauroot = os.path.expanduser(self.tauroot)
        except Exception:
            # TAU is optional
            self.tauroot = None

        self.threads = self.config.getint("%s.threads" % self.longname, 1)
        self.execmd = self.config.get("%s.exe_cmd" % self.longname)
        self.execmd = os.path.expanduser(self.execmd)
        if not os.path.isabs(self.execmd):
            self.execmd = os.path.join(self.cwd,self.execmd) # relative path provided
        self.exeopt = self.config.get("%s.exe_opt" % self.longname, "")

        self.ppkname = self.config.get("%s.ppkname" % self.longname, "data")

        self.specdirs = self.config.get("%s.specdirs" % self.longname, "").split()
        self.specdirs = list(map(os.path.expanduser, self.specdirs))
        self.specdirs = [os.path.join(self.cwd, specdir) for specdir in self.specdirs]

        self.metric_set = MetricSet(self.specdirs)
        self.parted_metrics = self.metric_set.nmetrics  # default value, not partitioned
        if not self.parted_metrics: self.parted_metrics=set("TIME")

        # init logger facility
        self.logger_init()

        # import submodules based on config options
        _module = import_module(".%s" % self.platform_name, package="autoperf.platforms")
        self.platform = _module.Platform(self)

        _module = import_module(".%s" % self.tool_name, package="autoperf.tools")
        self.tool = _module.Tool(self)

        _module = import_module(".%s" % self.datastore_name, package="autoperf.datastores")
        self.datastore = _module.Datastore(self)

        self.analyses = dict()
        for analysis_name in self.analyses_names:
            _module = import_module(".%s" % analysis_name, package="autoperf.analyses")
            self.analyses[analysis_name] = _module.Analysis(self)

        self.logger.info("")

    def logger_init(self):
        """
        Get logger configurations and set it up.
        """

        # log level
        loglvl = self.config.get("Logger.%s.loglvl" % self.name, "DEBUG")
        loglvl = os.environ.get("LOGLEVEL", getattr(logging, loglvl.upper(), None)) # Override with env var
        if not isinstance(loglvl, int):
            loglvl = logging.DEBUG
            self.logger.log(logging.WARN, "# Invalid log level. Using default value (DEBUG)")

        # self.logger = logging.getLogger(__name__)
        self.logger = logger.MyLogger(__name__, loglvl)

        # log destination
        logfile = self.config.get("Logger.%s.logfile" % self.logger.name,
                                  fix_path("%s/autoperf.log" % self.rootdir))

        # log formatter
        # formatter = logging.Formatter(fmt="%(asctime)s %(levelname)-7s %(message)s",
        #                               datefmt="%m-%d-%y %H:%M:%S")
        formatter = logging.Formatter()

        # log handler
        self.logHandler = logging.FileHandler(logfile)
        self.logHandler.setFormatter(formatter)
        self.logger.addHandler(self.logHandler)


        self.logger.setLevel(loglvl)

        self.logger.info("########## EXPERIMENT START ##########")
        self.logger.info("")
        self.logger.info("Name     : %s", self.name)
        self.logger.info("Platform : %s", self.platform_name)
        self.logger.info("Tool     : %s", self.tool_name)
        self.logger.info("Analyses : %s", self.analyses_names)
        self.logger.info("Rootdir  : %s", self.rootdir)
        self.logger.info("MPI      : %s", self.is_mpi)
        self.logger.info("CUPTI    : %s", self.is_cupti)
        self.logger.info("Instance : %s", self.insname)
        self.logger.info("LogLevel : %s", logging.getLevelName(self.logger.getEffectiveLevel()))

    def _get_status(self, experiment, dirname):
        """
        This helper function checks whether `dirname` contains a valid
        instance of `experiment`. If it does, return status of every
        iteration of the instance as a list. Return an empty list if
        no valid instance found.

        Args:
          dirname (string): A directory

        Returns:
          list: the status the instance
        """
        status = []

        # `dirname` should be in specific pattern (i.e. timestamp)
        if not re.match(r"\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{6}",
                        os.path.basename(dirname)):
            return status

        # now looking for the stat marker
        for item in os.listdir(dirname):
            # stat marker is not a directory
            if os.path.isdir(os.path.join("%s" % dirname, "%s" % item)):
                continue

            # experiment name is also encoded in stat marker name for
            # convenience
            m = re.match(r"\.job-(.+)-\d+\.stat", item)
            if m is None:
                continue
            else:
                expname = m.group(1)

            # be aware of that multiple experiments could share a
            # single rootdir, so let's make sure this instance belongs
            # to current experiment
            if expname != experiment:
                continue

            stat = {}
            marker = os.path.realpath(os.path.join("%s"%dirname, "%s"%item))

            if os.path.isfile(marker):
                with open(marker, 'r') as fp:
                    content = fp.read().split()
                    stat["marker"] = marker
                    stat["exp_name"] = content[0]
                    stat["insname"] = content[1]
                    stat["jobid"] = content[2]
                    stat["status"] = content[3]

            else:
                # small chance that job stat marker is not placed yet
                stat["marker"] = marker
                stat["exp_name"] = expname
                stat["insname"] = os.path.basename(dirname)
                stat["jobid"] = "Unknown"
                stat["status"] = "Unknown"

            # double check the job status, i.e. qdel? ctrl-c?
            if stat["status"] != "Finished" and stat["status"] != "Unknown":
                queue, colon, jobid = stat["jobid"].partition(":")

                # try our best, use the queue name saved in stat
                # marker instead of current config file
                _module = import_module(".%s" % queue, package="autoperf.queues")
                if _module.Queue(self).get_status(stat["jobid"]) == "Dead":
                    stat["status"] = "Aborted"

            status.append(stat)

        status.sort(key=lambda stat: stat["jobid"])
        return status

    def get_status(self, path='.'):
        """
        Search `path` for all instances of current experiment, get
        their status and return.

        Args:
          path (string): A directory path

        Returns:
          list: A list of status
        """
        stats = []

        dirs = [os.path.join(path, f) for f in os.listdir(path)]
        dirs = [d for d in dirs if os.path.isdir(d)]
        for dirname in dirs:
            stat = self._get_status(self.name, dirname);
            if len(stat) != 0:
                stats.append(stat)

        stats.sort(key=lambda stat: stat[0]["insname"])
        return stats

    def get_all_instances(self, expname=None):
        """
        Get all instances of an experiment.

        Args:
          expname (string): Name of an experiment

        Returns:
          list: A list of (instance_name, data_directory)
        """
        if expname is None:
            expname = self.name

        instances = []

        rootdir = os.path.expanduser(self.config.get("Experiments.%s.rootdir" % expname, self.cwd))
        self.rootdir = os.path.join(self.cwd, rootdir)

        dirs = [os.path.join(rootdir, f) for f in os.listdir(rootdir)]
        dirs = [d for d in dirs if os.path.isdir(d)]
        for dirname in dirs:
            stat = self._get_status(expname, dirname)
            if len(stat) != 0:
                instances.append((os.path.basename(dirname), dirname))

        instances.sort(key=lambda inst: inst[0])

        return instances

    def build(self):
        """
        Run the builder command if it exists
        """
        try:
            builder = self.config.get("%s.builder" % self.longname)
            builder = os.path.expanduser(builder)
        except configparser.Error:
            self.logger.verb("No builder found, bypass\n")
            return

        env = {
            'AP_ROOTDIR': self.rootdir,
            'AP_PLATFORM': self.platform_name,
            'AP_TOOL': self.tool_name,
        }

        env = dict(list(env.items()) + list(self.platform.build_env().items()))

        self.logger.info("Building the application")
        for key, val in list(env.items()):
            self.logger.cmd("export %s='%s'", key, val)
        self.logger.cmd(builder)

        process = subprocess.Popen(shlex.split(builder),
                                   env=dict(list(os.environ.items()) + list(env.items())))

        for key in env:
            self.logger.cmd("unset %s", key)
        self.logger.cmd("")

        returncode = process.wait()
        if returncode != 0:
            raise Exception("Builder failed")

    def setup(self):
        """
        This is the second step of the initialization. We setup
        submodules after they have all been instantiated.
        """
        self.platform.setup()
        self.tool.setup()
        self.datastore.setup()

        for a in self.analyses.values():
            a.setup()

        # now populate the metric set we need to measure
        for a in self.analyses.values():
            for m in a.longmetrics:
                self.metric_set.add(m)

    def link_items(self):
        """
        Link necessary files, if they are specified in config file
        """
        try:
            items = self.config.get("%s.link" % self.longname).split()
        except configparser.Error:
            self.logger.verb("Nothing to link, bypass\n")
            return

        self.logger.info("Linking necessary files")
        for item in items:
            print("Linking %s ..." % item)
            item = os.path.normpath(item)
            item = os.path.expanduser(item)
            link_name = os.path.basename(item)
            if os.path.islink(link_name) and os.readlink(link_name) == item:
                # do nothing if the link is already there
                self.logger.verb("Link name is already there: %s", link_name)
            else:
                self.logger.cmd("ln -s %s %s", item, link_name)
                os.symlink(item, link_name)

    def copy_items(self):
        """
        Copy necessary files, if they are specified in config file
        """
        try:
            items = self.config.get("%s.copy" % self.longname).split()
        except configparser.Error:
            self.logger.verb("Nothing to copy, bypass\n")
            return

        self.logger.info("Copying necessary files")
        for item in items:
            print("Copying %s ..." % item)
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
        print("--- Preparing to run %s" % self.name)

        # logger
        self.logger.info("Run the experiment")
        self.logger.cmd("function run-%s () {", self.insname)
        self.logger.shift()
        # 'cd' actually happens in __init__()
        self.logger.cmd("cd %s\n", self.rootdir)

        # link, copy and build
        self.link_items()
        self.copy_items()
        self.build()

        # TODO: temporarily disabling until the default non-counter configuration works
        if False:
            # partition the metrics
            from ..ext import partitioner
            dbfile = self.config.get("Partitioner.%s.dbfile" % self.name, "%s.db" % self.platform_name)
            algo = self.config.get("Partitioner.%s.algo" % self.name, "greedy")
            self.parted_metrics = partitioner(dbfile, list(self.metric_set.nmetrics), algo, False)

            # logger
            self.logger.info("Partitioning the metrics:")
            if len(self.parted_metrics) == 0:
                self.logger.critical("CRITICAL: partitioner failed, abort\n")
                # 'cd' actually never happens
                self.logger.cmd("cd %s", self.cwd)
                self.logger.unshift()
                self.logger.cmd("}")
                raise Exception("Metrics partition failed!")
            for i in range(len(self.parted_metrics)):
                self.logger.info("  %2d: %s", i + 1, self.parted_metrics[i])
            self.logger.newline()

        # populate the data directories
        self.logger.info("Populating data directories")
        profiles_path = fix_path("%s/profiles/" % self.insname)
        self.logger.cmd("mkdir -p %s", profiles_path)
        os.makedirs("%s" % profiles_path)

        self.datadirs = []
        for i in range(len(self.parted_metrics)):
            datadir = fix_path("%s/.iter-%02d" % (self.insname, i))
            self.datadirs.append(datadir)

            self.logger.cmd("mkdir -p %s/profiles", datadir)
            os.makedirs(fix_path("%s/profiles" % datadir))

            # pre-link job log and stat marker
            target = os.path.relpath(fix_path("%s/job.log" % datadir), self.insname)
            link_name = fix_path("%s/job-%02d.log" % (self.insname, i))
            self.logger.cmd("ln -s %s %s", target, link_name)
            try:
                os.symlink(target, link_name)
            except:
                pass
            target = os.path.relpath(fix_path("%s/.job.stat" % datadir), self.insname)
            link_name = fix_path("%s/.job-%s-%02d.stat" % (self.insname, self.name, i))
            self.logger.cmd("ln -s %s %s", target, link_name)
            try:
                os.symlink(target, link_name)
            except:
                pass
        self.logger.newline()

        # run the experiment
        for i in range(len(self.parted_metrics)):
            self.logger.info("Running experiment, iteration %d of %d",
                             i + 1, len(self.parted_metrics))
            self.iteration = i
            self.platform.run(self.execmd, self.exeopt, block)
            self.logger.newline()

        # 'cd' actually happens in cleanup()
        self.logger.cmd("cd %s", self.cwd)
        self.logger.unshift()
        self.logger.cmd("}")

    def analyze(self):
        # sanity check
        if self.insname is None:
            self.logger.critical("CRITICAL: do not know the instanceId of the experiment, abort")
            raise Exception("Do not know the instanceId of the experiment")

        # logger
        self.logger.info("Analyze the experiment")
        self.logger.cmd("function analyze-%s () {", self.insname)
        self.logger.shift()
        # 'cd' actually happens in __init__()
        self.logger.cmd("cd %s\n", self.rootdir)

        # we need to re-discover data directories if we are not
        # running in block mode
        if len(self.datadirs) == 0:
            for d in os.listdir(self.insname):
                if not os.path.isdir("%s/%s" % (self.insname, d)):
                    continue
                if not re.match(r"\.iter-\d+$", d):
                    continue
                self.datadirs.append("%s/%s" % (self.insname, d))
            self.datadirs.sort()

        # collect generated data and do the post-processing
        self.platform.collect_data()

        # run the analyses
        self.logger.info("Running the analyses:")
        for analysis in list(self.analyses.values()):
            analysis.run()

        # logger
        self.logger.newline()
        # 'cd' actually happens in cleanup()
        self.logger.cmd("cd %s", self.cwd)
        self.logger.unshift()
        self.logger.cmd("}")

    def cleanup(self):
        os.chdir(self.cwd)

        self.logger.info("")
        self.logger.info("########## EXPERIMENT END   ##########")
        self.logger.newline()

        self.logger.removeHandler(self.logHandler)
