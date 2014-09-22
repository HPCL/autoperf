import os
import re

class AbstractQueue:
    name       = "Abstract"
    longname   = "Abstract"
    experiment = None

    def __init__(self, experiment):
        raise NotImplementedError

    def setup(self):
        raise NotImplementedError

    def submit(self, cmd, block=False):
        raise NotImplementedError

    def _check(self, instance):
        if not re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}T\d{3}",
                        instance):
            return None

        status = "%s/job.stat" % instance
        if not os.path.isfile(status):
            return None

        fp = open(status, 'r')
        stat = fp.read().split()
        fp.close()

        if stat[0] == self.experiment.name:
            return stat
        else:
            return None

    def check(self, path='.'):
        stats = [ ]
        dirs  = [f for f in os.listdir(path) if os.path.isdir(f)]

        for dirname in dirs:
            stat = self._check(dirname)
            if stat is None:
                continue

            stats.append(stat)
            if stat[1] == self.experiment.insname:
                return [stat]

        if self.experiment.insname is None:
            stats.sort(key=lambda stat: stat[1])
            return stats
        else:
            return [ ]
