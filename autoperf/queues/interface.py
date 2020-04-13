class AbstractQueue:
    name = "Abstract"
    longname = "Abstract"
    experiment = None

    def get_status(self, idstr):
        raise NotImplementedError

    @staticmethod
    def cancel(iteration):
        raise NotImplementedError

    def __init__(self, experiment):
        raise NotImplementedError

    def setup(self):
        raise NotImplementedError

    def submit(self, cmd, block=False):
        raise NotImplementedError

    def wrap_command(self, execmd, exeopt):
        return [execmd, exeopt]
