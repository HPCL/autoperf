import logging

class MyLogger(object):
    VERB = 15
    VERBOSE = 15

    CMD = 12
    COMMAND = 12

    indent = ""

    def __init__(self, name, level=logging.DEBUG):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logHandler = None

    def shift(self):
        if self.logger.isEnabledFor(self.CMD):
            self.indent = "    %s" % self.indent

    def unshift(self):
        if self.logger.isEnabledFor(self.CMD):
            self.indent = self.indent[:-4]

    def newline(self):
        self.logger.critical("")

    def verb(self, msg, *args, **kwargs):
        msg = "%s# %s" % (self.indent, msg)
        self.logger.log(level=MyLogger.VERB, msg=msg)

    def cmd(self, msg, *args, **kwargs):
        print(self.getEffectiveLevel())
        msg = "%s%s" % (self.indent, msg)
        self.logger.log(level=MyLogger.CMD, msg=msg)

    def debug(self, msg, *args, **kwargs):
        msg = "%s# %s" % (self.indent, msg)
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        msg = "%s# %s" % (self.indent, msg)
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        msg = "%s# %s" % (self.indent, msg)
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        msg = "%s# %s" % (self.indent, msg)
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        msg = "%s# %s" % (self.indent, msg)
        self.logger.critical(msg, *args, **kwargs)

    def addHandler(self, handler):
        self.logHandler = handler
        self.logger.addHandler(handler)

    def removeHandler(self, handler):
        self.logger.removeHandler(handler)

    def setLevel(self, level):
        self.logger.setLevel(level)

    def getEffectiveLevel(self):
        return self.logger.getEffectiveLevel()