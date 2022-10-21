# Assuming you have not changed the general structure of the template no modification is needed in this file.
from .install_requirements import pip_install, setup_install
from pathlib import Path

pip_install(["numpy", "pandas", "scipy"])

setup_install([
    Path(__file__).parent / "geometry", 
    ])

from .lib.special_utils import tag_methods
tag_methods()

from . import commands
from .lib import fusion360utils as futil


def run(context):
    try:
        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.start()

    except:
        futil.handle_error('run')


def stop(context):
    try:
        # Remove all of the event handlers your app has created
        futil.clear_handlers()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.stop()

    except:
        futil.handle_error('stop')