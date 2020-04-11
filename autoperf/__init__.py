import logging

from .utils.logger import MyLogger

# use customized logger
logging.setLoggerClass(MyLogger)
logging.VERB = MyLogger.VERB
logging.VERBOSE = MyLogger.VERBOSE
logging.CMD = MyLogger.CMD
logging.COMMAND = MyLogger.COMMAND
logging.addLevelName(MyLogger.VERB, "VERB")
logging.addLevelName(MyLogger.CMD, "CMD")

logger = logging.getLogger(__name__)
