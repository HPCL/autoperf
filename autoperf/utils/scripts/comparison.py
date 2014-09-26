#!/usr/bin/env jython

import os, re
import sys
import subprocess

from glob import glob

TAUROOT = "{tauroot}"

# name of the instance A and B
aName = "{aName}"
bName = "{bName}"

# directory holding instance A and B
aDir  = "{aDir}"
bDir  = "{bDir}"

# metrics we are going to compare
metrics = {metrics}

# data filter parameters
mode      = "{mode}"
throttle  = {throttle}
threshold = {threshold}

# TAUdb config name
taudb   = "{taudb}"

# import all necessary JARs ...
for jar in glob("%s/lib/*.jar" % TAUROOT):
    sys.path.append(jar)

# ... so that we can use them here
from edu.uoregon.tau.perfdmf import DataSourceExport
from edu.uoregon.tau.perfdmf.taudb import TAUdbDatabaseAPI
from edu.uoregon.tau.perfdmf.taudb import TAUdbDataSource
from edu.uoregon.tau.perfexplorer.glue import *

from java.io   import File

class Error(Exception):
    pass

class DBFailure(Error):
    def __str__(self):
        return "Can not connect to the database"

class NoSuchTrial(Error):
    def __init__(self, trialName):
        self.trialName = trialName
    def __str__(self):
        return "%s: Can not find such trial" % self.trialName

# gnuplot script template
gp_template = """#!/usr/bin/env gnuplot

# reset all config
reset

numEvents = {{numEvents}}
maxLen    = {{maxLen}}

# calculate the proper size of canvas
X = (64*numEvents) > 640 ? (64*numEvents) : 640
Y = 480 + 12*maxLen

set terminal png size X, Y font 'Monospace' 10
set output '{{metric}}.png'

# palette

set style line 1 lc rgb '#D53E4F' # red
set style line 2 lc rgb '#F46D43' # orange
set style line 3 lc rgb '#FDAE61' # pale orange
set style line 4 lc rgb '#FEE08B' # pale yellow-orange
set style line 5 lc rgb '#E6F598' # pale yellow-green
set style line 6 lc rgb '#ABDDA4' # pale green
set style line 7 lc rgb '#66C2A5' # green
set style line 8 lc rgb '#3288BD' # blue

set palette defined ( 0 '#D53E4F',\\
		      1 '#F46D43',\\
		      2 '#FDAE61',\\
		      3 '#FEE08B',\\
		      4 '#E6F598',\\
		      5 '#ABDDA4',\\
		      6 '#66C2A5',\\
		      7 '#3288BD' )

# graph borders
set border 3

set size .9, .9

set auto y
set grid ytics

# histogram styling
set style data histogram
set style histogram cluster gap 1
set style fill solid noborder
set boxwidth 0.9

set logscale y
set xtics nomirror rotate scale 0
set ytics nomirror rotate by 45
set ylabel "{{metric}}"

# ploting!
plot 'compare.{{metric}}.dat' using 1:xticlabels(3) title columnhead ls 1, \\
     'compare.{{metric}}.dat' using 2               title columnhead ls 8
"""

def load_result(taudbCfg, trialName, trialDir):
    """
    Load a trial result with the given name. If find a local ppk file
    with the name 'data.ppk', use it. Otherwise, try to connect
    to TAUdb using `taudbCfg`, export the trial named `trialName` to a
    local ppk file and then load it.

    Args:
      taudbCfg  (string): Name of the TAUdb config we are going to try
      trialName (string): Name of the trial we want to load
      trialDir  (string): Directory to look for 'data.ppk'

    Returns:
      The trial data we load

    Exceptions:
      DBFailure  : Can not connect to TAUdb
      NoSuchTrial: The trial can not be found
    """
    ppk = "%s/data.ppk" % trialDir
    cfg = os.path.expanduser("~/.ParaProf/perfdmf.cfg.%s" % taudbCfg)

    if os.path.isfile(ppk) is False:
        print "*** Exporting trial %s from taudb ..." % trialName,

        # connect to TAUdb
        db = TAUdbDatabaseAPI()
        db.initialize(cfg, False)

        try:
            trial = db.setTrial(trialName, True)
        except:
            raise DBFailure

        if trial is None:
            raise NoSuchTrial(trialName)

        data = TAUdbDataSource(db)
        data.load()
        # data.generateDerivedData()

        DataSourceExport.writePacked(data, File(ppk))

        print "Done"

    print "*** Loading trial %s ..." % trialName
    result = DataSourceResult(DataSourceResult.PPK,
                              [ppk],
                              False)
    result.setIgnoreWarnings(True)
    print "*** Done"

    return result

def trim_annotation(eventName):
    # trim leading annotations
    eventName = re.sub(r'^(\[.*?\])*', '', eventName)

    # trim tailing annotations
    eventName = re.sub(r'\[\{{.*?\}}\]', '', eventName)

    return '"' + eventName.strip() + '"'

def compare(aResult, bResult, metric):
    global mode
    global throttle
    global threshold

    aEvents = aResult.getEvents()
    bEvents = bResult.getEvents()

    events  = list(set(aEvents) | set(bEvents))

    aData   = {{ }}
    bData   = {{ }}
    absDiff = {{ }}
    relDiff = {{ }}

    # get metric data for all events
    for event in set(aEvents) - set(bEvents):
        bData[event] = 0
    for event in set(bEvents) - set(aEvents):
        aData[event] = 0
    for event in aEvents:
        aData[event] = aResult.getDataPoint(0, event, metric, aResult.EXCLUSIVE)
    for event in bEvents:
        bData[event] = bResult.getDataPoint(0, event, metric, bResult.EXCLUSIVE)

    # calculate absolute and relative difference
    for event in events:
        absDiff[event] = abs(bData[event] - aData[event])
        relDiff[event] = absDiff[event] / aData[event]

    # prepare for the filter
    if mode == "absolute":
        diff = absDiff.items()
    else:
        diff = relDiff.items()

    # apply the throttle
    def throttle_filter(item):
        event = item[0]
        return (aData[event] >= throttle) or (bData[event] >= throttle)
    diff = filter(throttle_filter, diff)

    # apply the threshold
    diff.sort(key=lambda item: -item[1])
    events = [item[0] for item in diff[:threshold]]

    # write the gnuplot data file
    maxLen = 0
    fmtstr = "{{0:<30}}   {{1:<30}}   {{2}}\n"
    f = open("compare.%s.dat" % metric, "w")
    f.write(fmtstr.format(aName, bName, "EventName"))
    for event in events:
        eventName = trim_annotation(event)
        maxLen = max(maxLen, len(eventName)-2)
        f.write(fmtstr.format(aData[event], bData[event], eventName))
    f.close()

    # write the gnuplot script
    f = open("%s.gp" % metric, "w")
    f.write(gp_template.format(metric=metric, numEvents=len(events), maxLen=maxLen))
    f.close()

    # run the gnuplot script
    subprocess.call(["gnuplot", "%s.gp" % metric])

if __name__ == "__main__":
    os.chdir(bDir)

    aResult = load_result(taudb, aName, aDir)
    bResult = load_result(taudb, bName, bDir)

    aStatistics = BasicStatisticsOperation(aResult).processData()
    bStatistics = BasicStatisticsOperation(bResult).processData()

    aMean = aStatistics[BasicStatisticsOperation.MEAN]
    bMean = bStatistics[BasicStatisticsOperation.MEAN]

    for metric in metrics:
        compare(aMean, bMean, metric)
