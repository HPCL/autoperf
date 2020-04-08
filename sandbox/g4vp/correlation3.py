import os
import numpy as np

import matplotlib
# get rid of "no display name" error
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from itertools import product
from math import isnan, isinf

from ..utils.PPK import PPK
from ..utils     import config
from .interface  import AbstractAnalysis

class Analysis(AbstractAnalysis):
    """Correlation between different metrics for several experiments"""

    def __init__(self, experiment):
        self.name       = "correlation3"
        self.longname   = "Analyses.%s.%s" % (self.name, experiment.name)
        self.experiment = experiment

        # option format:
        #   metrics = m1:m2 m3:m4
        # which means get correlation between m1 and m2, m3 and m4
        self.pairs = config.get("%s.metrics" % self.longname).split()
        self.pairs = [p.split(':') for p in self.pairs]
        self.metrics = [m for sublist in self.pairs for m in sublist]
        self.metrics = list(set(self.metrics))
        self.longmetrics = self.metrics

        self.hotspots  = config.get("%s.hotspots"  % self.longname, "").split()
        self.instance  = config.get("%s.instance"  % self.longname)

    def setup(self):
        pass

    def correlation(self, m, n, zoomin=False, trim=True):
        area = 2000
        filename = "cor3_%s_%s.png" % (m, n)

        plt.figure()

        if zoomin:
            area *= 10
            filename = "cor3_%s_%s_zoomin.png" % (m, n)
            plt.axis([0, 1e9, 0, 3])
            ax = plt.gca()
            ax.set_autoscale_on(False)

        plt.xlabel(m)
        plt.ylabel(n)
        plt.grid(True)

        # "i"ndex of metric "m" or "n" for ppk "a"
        ima = self.aPPK.metrics.index(m)
        ina = self.aPPK.metrics.index(n)

        # "d"ata of metric "m" or "n" for ppk "a"
        dma = self.aPPK.aggExcArray[PPK.MEAN][:, ima]
        dna = self.aPPK.aggExcArray[PPK.MEAN][:, ina]

        if trim:
            # ignore zero, inf and NaN for both x and y axis
            mask = np.ones(len(dma), dtype=bool)
            for i in range(len(dma)):
                if dma[i] == 0 or dna[i] == 0 or isnan(dma[i]) or isnan(dna[i]) or isinf(dma[i]) or isinf(dna[i]):
                    mask[i] = False
            dma = dma[mask]
            dna = dna[mask]

            # "e"vents for ppk "a"
            ea = list(np.array(self.aPPK.aggEvents)[mask])
            #ea = [a for (a,b) in zip(self.aPPK.aggEvents, mask) if b]
        else:
            ea = self.aPPK.aggEvents

        # "i"ndex of metric "m" or "n" for ppk "b"
        imb = self.bPPK.metrics.index(m)
        inb = self.bPPK.metrics.index(n)

        # "d"ata of metric "m" or "n" for ppk "b"
        dmb = self.bPPK.aggExcArray[PPK.MEAN][:, imb]
        dnb = self.bPPK.aggExcArray[PPK.MEAN][:, inb]

        if trim:
            # ignore zero, inf and NaN for both x and y axis
            mask = np.ones(len(dmb), dtype=bool)
            for i in range(len(dmb)):
                if dmb[i] == 0 or dnb[i] == 0 or isnan(dmb[i]) or isnan(dnb[i]) or isinf(dmb[i]) or isinf(dnb[i]):
                    mask[i] = False
            dmb = dmb[mask]
            dnb = dnb[mask]

            # "e"vents for ppk "b"
            eb = list(np.array(self.bPPK.aggEvents)[mask])
            #eb = [a for (a,b) in zip(self.bPPK.aggEvents, mask) if b]
        else:
            eb = self.aPPK.aggEvents

        plt.scatter(dma, dna, c="r", alpha=0.6, s=(dma/dma.sum())*area)
        plt.scatter(dmb, dnb, c="g", alpha=0.6, s=(dmb/dmb.sum())*area)


        ############ add annotation ##############

        index = list(range(len(ea)))
        index = [y for (x,y) in sorted(zip(dma, index), reverse=True)]
        index = index[:5]       # top 5

        for i in range(len(index)):
            j = index[i]

            #import pdb; pdb.set_trace()

            plt.annotate(i, xy=(dma[j], dna[j]), xytext=(-10, 10), 
                         textcoords='offset points', ha='right', va='bottom',
                         bbox = dict(boxstyle = 'round,pad=0.2', fc = 'red', alpha = 0.3),
                         arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'),
                         fontsize=8)

            event = ea[j]
            try:
                k = eb.index(event)
                plt.annotate(i, xy=(dmb[k], dnb[k]), xytext=(-10, 10), 
                             textcoords='offset points', ha='right', va='bottom',
                             bbox = dict(boxstyle = 'round,pad=0.2', fc = 'green', alpha = 0.3),
                             arrowprops = dict(arrowstyle = '->', connectionstyle = 'arc3,rad=0'),
                             fontsize=8)
            except ValueError:
                # this event is not in ppk "b", ignore it
                print "Ender: %s not in b" % event
                pass
            
        plt.savefig(filename)

        plt.close()

    def run(self):
        self.aName  = self.instance
        self.aDir   = os.path.join(os.getcwd(), self.aName)

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

        for m, n in self.pairs:
            print "cor3 for %s and %s" % (m, n)
            self.correlation(m, n, False)
            self.correlation(m, n, True)

        os.chdir(cwd)
