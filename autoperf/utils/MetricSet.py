import os

from MathExp import MathExp

class MetricSet:
    def __init__(self):
        self.nmetrics = set()   # set : name of native metrics we depend on
        self.interval = { }     # map : nmetric name => sampling interval (for hpctoolkit)
        self.dmetrics = [ ]     # list: name of derived metric
        self.rpns     = { }     # map : dmetric name => list of MathExp

    def is_derived(self, metric):
        natives = ['TIME']

        if metric.startswith('PAPI_'):
            return False

        if metric.upper() in natives:
            return False

        return True

    def get_metric_spec(self, metric):
        this_dir, this_file = os.path.split(__file__)
        spec_file = "%s/metric_spec/%s" % (this_dir, metric)

        contents = [ ]
        with open(spec_file, "r") as f:
            for line in f:
                line = line.strip()

                # ignore empty line
                if len(line) == 0:
                    continue

                # ignore comments
                if line[0] is '#':
                    continue

                contents.append(line)

        return contents

    def add_derived_metric(self, metric, interval):
        if metric in self.dmetrics:
            return

        if not self.is_derived(metric):
            return

        exps = [ ]

        for spec in self.get_metric_spec(metric):
            exp = MathExp(spec)

            variables = [v for v in exp.variables if self.is_derived(v)]

            map(self.add, variables)
            exps.append(exp)

            metrics = [v for v in exp.variables if not self.is_derived(v)]

            self.nmetrics |= set(metrics)
            for m in metrics:
                self.interval[m] = interval

        if len(exps) == 0:
            raise Exception("Empty spec for derived metric `%s`" % metric)

        self.dmetrics.append(metric)
        self.rpns[metric] = exps

    def add(self, lmetric):
        p = lmetric.partition('@')

        metric = p[0]
        if p[2] is '':
            interval = 1000
        else:
            interval = p[2]

        if self.is_derived(metric):
            self.add_derived_metric(metric, interval)
        else:
            self.nmetrics.add(metric)
            self.interval[metric] = interval

    def eval(self, symtab):
        rv = { }                # map: dmetric name => value
        for metric in self.dmetrics:
            if metric in symtab:
                val = symtab[metric]
            else:
                for rpn in self.rpns[metric]:
                    val = rpn.eval(symtab)

            rv[metric]     = val
            symtab[metric] = val

        return rv
