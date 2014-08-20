import os

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

    def _check(self, file):
        if file.startswith("running."):
            fp = open(file, 'r')
            job_id = fp.read()
            fp.close()
            return {'job_id': job_id,
                    'insname': file[8:],
                    'stat': 'Running'}

        if file.startswith("finished."):
            fp = open(file, 'r')
            job_id = fp.read()
            fp.close()
            return {'job_id': job_id,
                    'insname': file[9:],
                    'stat': 'Finished'}
        return None

    def check(self, path='.'):
        stats = [ ]
        files = [f for f in os.listdir(path) if os.path.isfile(f)]

        for file in files:
            stat = self._check(file)
            if stat is not None:
                stats.append(stat)
                # print "%s ==? %s" % (stat['insname'], self.experiment.insname)
                if stat['insname'] == self.experiment.insname:
                    return [stat]

        if self.experiment.insname is None:
            return stats
        else:
            return [ ]
