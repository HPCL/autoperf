import os
import subprocess

def run(template, script, **kwargs):
    """
    Run a script populated from a template

    Args:
      template (string): A template file which will be interpreted as
                         a python format string
      script   (string): The populated script file
      kwargs   (kwargs): Keyword arguments used to populate `script`
                         from the `template`

    Returns:
      None
    """
    delete = False
    this_dir, this_file = os.path.split(__file__)

    if script is None:
        script = '.script'
        delete = True

    f = open("%s/scripts/%s" % (this_dir, template), "r")
    content = f.read().format(**kwargs)
    f.close()

    f = open(script, 'w')
    f.write(content)
    f.close()
    os.chmod(script, 0755)

    subprocess.call(os.path.realpath(script))

    if delete:
        os.unlink(script)
