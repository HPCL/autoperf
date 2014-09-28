from logging import Logger

class MyLogger(Logger):
    VERB    = 15
    VERBOSE = 15

    CMD     = 12
    COMMAND = 12

    indent = ""

    def __init__(self, name):
        Logger.__init__(self, name)

    def shift(self):
        if self.isEnabledFor(self.CMD):
            MyLogger.indent = "    %s" % MyLogger.indent

    def unshift(self):
        if self.isEnabledFor(self.CMD):
            MyLogger.indent = MyLogger.indent[:-4]

    def newline(self):
        Logger.critical(self, "")

    def verb(self, msg, *args, **kwargs):
        msg = "%s# %s" % (MyLogger.indent, msg)
        Logger.log(self, self.VERB, msg, *args, **kwargs)

    def cmd(self, msg, *args, **kwargs):
        msg = "%s%s" % (MyLogger.indent, msg)
        Logger.log(self, self.CMD, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        msg = "%s# %s" % (MyLogger.indent, msg)
        Logger.debug(self, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        msg = "%s# %s" % (MyLogger.indent, msg)
        Logger.info(self, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        msg = "%s# %s" % (MyLogger.indent, msg)
        Logger.warning(self, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        msg = "%s# %s" % (MyLogger.indent, msg)
        Logger.error(self, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        msg = "%s# %s" % (MyLogger.indent, msg)
        Logger.critical(self, msg, *args, **kwargs)
