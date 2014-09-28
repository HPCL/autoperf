import os
import logging
import subprocess

logger = logging.getLogger(__name__)

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
    global logger
    delete = False
    this_dir, this_file = os.path.split(__file__)

    if script is None:
        script = '.script'
        delete = True

    logger.info("Populating a helper script (%s) from the template (%s)", script, template)

    with open("%s/scripts/%s" % (this_dir, template), "r") as f:
        content = f.read().format(**kwargs)

    with open(script, 'w') as f:
        f.write(content)

    os.chmod(script, 0755)

    logger.info("Running the helper script (%s)", script)
    logger.cmd(os.path.relpath(script))

    subprocess.call(os.path.relpath(script))

    if delete:
        os.unlink(script)
