import os, subprocess

class AbstractAnalysis:
    metrics = [ ]

    def __init__(self, experiment):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError

    def run_script(self, script, **kwargs):
        this_dir, this_file = os.path.split(__file__)

        f = open("%s/scripts/%s" % (this_dir, script), "r")
        content = f.read().format(**kwargs)
        f.close()

        analyzer = open(script, 'w')
        analyzer.write(content)
        analyzer.close()
        os.chmod(script, 0755)

        subprocess.call("./%s" % script)

