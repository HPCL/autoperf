#!/usr/bin/env jython

import sys

TAULIB = "{TAULIB}"

sys.path.append(TAULIB+"/perfexplorer.jar")
sys.path.append(TAULIB+"/perfdmf.jar")
sys.path.append(TAULIB+"/tau-common.jar")

from edu.uoregon.tau.perfexplorer.glue import *
from edu.uoregon.tau.perfdmf import Trial
from edu.uoregon.tau.perfexplorer.client import PerfExplorerModel

from java.util import HashSet
from java.util import ArrayList
from java.util.regex import Pattern
from java.util.regex import Matcher

def dump(result):
    threads = result.getThreads()
    events  = result.getEvents()
    metrics = result.getMetrics()

    for thread in threads:
        for event in events:
            for metric in metrics:
                data = result.getDataPoint(thread, event, metric, result.EXCLUSIVE)
                print "%s : %s : %s : %s" % (thread, event, metric, data)

if __name__ == '__main__':
    derived_metrics = {derived_metrics}

    result = DataSourceResult(DataSourceResult.PPK, ["{ppk}"], False)

    dump(result)

    for name, metric in derived_metrics.items():
        d_result = DeriveMetricEquation(result, metric, name).processData()
        map(dump, d_result)
