
import os
import sys
import subprocess
import pkg_resources
from pathlib import Path


def pip_install(required):
    installed = set([pkg.key for pkg in pkg_resources.working_set])
    missing  = set(required) - installed

    if missing:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing])



def setup_install(paths):

    for path in paths:
        sys.path.append(str(path))


