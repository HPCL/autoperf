import os
import re
import subprocess

from ..utils.PPK import PPK
from ..utils     import config
from .interface  import AbstractAnalysis

class Analysis(AbstractAnalysis):

    # gnuplot script template
    gp_template = """#!/usr/bin/env gnuplot

# reset all config
reset

numEvents = {numEvents}
maxLen    = {maxLen}

# calculate the proper size of canvas
X = (64*numEvents) > 640 ? (64*numEvents) : 640
Y = 480 + 12*maxLen

set terminal png size X, Y 
set output '{metric}.png'

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
set ylabel "{metric}"

# ploting!
plot 'compare.{metric}.dat' using 1:xticlabels(3) title columnhead ls 1, \\
     'compare.{metric}.dat' using 2               title columnhead ls 8
"""

    def __init__(self, experiment):
        self.name       = "compare2"
        self.longname   = "Analyses.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        self.longmetrics = config.get("%s.metrics" % self.longname, "TIME").split()
        self.metrics     = [m.partition('@')[0] for m in self.longmetrics]

        self.mode      = config.get("%s.mode"      % self.longname, "absolute")
        self.throttle  = config.get("%s.throttle"  % self.longname, 1000)
        self.threshold = config.get("%s.threshold" % self.longname, 10)
        self.base      = config.get("%s.base"      % self.longname)
        self.hotspots  = config.get("%s.hotspots"  % self.longname, "").split()

    def setup(self):
        self.aName     = config.get("%s.instance"  % self.longname, "last")

        instances = self.experiment.get_all_instance(self.base)
        if len(instances) == 0:
            raise Exception("Can not find any instance of experiment '%s'" % self.base)

        if self.aName == "last":
            self.aName, self.aDir = instances[-1]
        else:
            for n, d in instances:
                if self.aName == n:
                    self.aDir = d
                    break

    def compare2(self, metric):
        aEvents = self.aPPK.aggEvents
        bEvents = self.bPPK.aggEvents

        events = list(set(aEvents) | set(bEvents))

        aData   = { }
        bData   = { }
        absDiff = { }
        relDiff = { }

        for event in events:
            aData[event] = self.aPPK.getAggExcMean(event, metric)
            bData[event] = self.bPPK.getAggExcMean(event, metric)

            absDiff[event] = abs(bData[event] - aData[event])

            # FIXME: Avoid devide-by-zero error. Is this the right
            # thing to do?
            if aData[event] == 0:
                relDiff[event] = absDiff[event] / 1
            else:
                relDiff[event] = absDiff[event] / aData[event]

        if self.mode == "absolute":
            diff = absDiff.items()
        else:
            diff = relDiff.items()

        # apply the throttle
        def throttle_filter(item):
            event = item[0]
            return (aData[event] >= int(self.throttle)) and (bData[event] >= int(self.throttle))
        diff = filter(throttle_filter, diff)


        # apply the threshold
        diff.sort(key=lambda item: -item[1])
        events = [item[0] for item in diff[:int(self.threshold)]]

        # write the gnuplot data file
        maxLen = 0
        fmtstr = "{0:<30}   {1:<30}   \"{2}\"\n"
        f = open("compare.%s.dat" % metric, "w")
        f.write(fmtstr.format(self.aName, self.bName, "EventName"))
        for event in events:
            maxLen = max(maxLen, len(event)-2)
            f.write(fmtstr.format(aData[event], bData[event], event))
        f.close()

        # write the gnuplot script
        f = open("%s.gp" % metric, "w")
        f.write(self.gp_template.format(metric=metric, numEvents=len(events), maxLen=maxLen))
        f.close()

        # run the gnuplot script
        subprocess.call(["gnuplot", "%s.gp" % metric])

    def run(self):
        self.bName  = self.experiment.insname
        self.bDir   = os.path.join(os.getcwd(), self.bName)

        self.aPPK = PPK("%s/data.ppk" % self.aDir, self.hotspots)
        self.bPPK = PPK("%s/data.ppk" % self.bDir, self.hotspots)

        self.aPPK.attachMetricSet(self.experiment.metric_set)
        self.bPPK.attachMetricSet(self.experiment.metric_set)

        self.aPPK.populateAggData();
        self.bPPK.populateAggData();

        cwd = os.getcwd()
        os.chdir(self.bDir)

        for metric in self.metrics:
            self.compare2(metric)

        os.chdir(cwd)
