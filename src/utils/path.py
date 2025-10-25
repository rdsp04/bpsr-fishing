import sys
from pathlib import Path
import os


def get_data_dir():
    """
    Returns the folder where data files should be stored.
    Uses current directory if running as script.
    Uses AppData/Local if running as frozen executable.
    """
    if getattr(sys, "frozen", False):
        # Executable path
        return Path(sys.executable).parent
    else:
        # Script path
        return Path.cwd()
