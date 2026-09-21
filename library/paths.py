"""
paths.py
========
Path helpers for the control library package.

WHAT: two small functions that answer "where is this package installed?"
and "give me the controls folder, creating it if needed". The library
never hardcodes a disk path - it resolves its own location at runtime
from __file__, so the repo can be cloned anywhere and mounted on
MAYA_SCRIPT_PATH.

WHY: course reference M2-L09.12 (Libreria de controles I) - the export
flow needs the package dir, the import flow needs the controls dir, and
both must work on any machine without touching code.

These functions RAISE on bad input (unlike qc/ setup/ tools that warn
and return): this is library code running under main.py / gui.py, which
catch and report. Library code fails loud, UI code fails friendly.

Usage:
    from library import paths
    pkg_dir = paths.getCurrentDir(__file__)
    lib_dir = paths.createDir(path=pkg_dir, directory="_control_lib")
"""

import os


def getCurrentDir(target=""):
    """
    Brief: absolute directory that contains the target file.

    Args:
        target (str): path of a file - usually this module's __file__,
            the reserved variable that stores the module AS a file.

    Returns:
        str: normalized absolute directory path.
    """
    return os.path.dirname(os.path.normpath(target))


def createDir(path="", directory="", silent=False):
    """
    Brief: create <path>/<directory> and return it. If the folder
    already exists, just return it (idempotent - safe on startup).

    Args:
        path (str): parent directory. Must already exist.
        directory (str): folder to create inside path.
        silent (bool): True mutes the "folder created" message, for
            when this runs inside a larger process.

    Returns:
        str: the final directory path.

    Raises:
        ValueError: empty path or directory.
        OSError: path does not exist, or os.makedirs failed
            (permissions and similar).
    """
    if not path:
        raise ValueError("paths.createDir: you must pass a path.")
    if not directory:
        raise ValueError("paths.createDir: you must pass a directory.")
    if not os.path.exists(path):
        raise OSError(f"paths.createDir: path does not exist: {path}")

    # os.listdir returns bare names (no path prefix), so a plain
    # membership check is enough to know the folder is already there.
    entries = os.listdir(path)
    finalDir = os.path.join(path, directory)
    if directory in entries:
        return finalDir

    try:
        os.makedirs(finalDir)
    except OSError as e:
        # Re-raise with our own message: permissions issues land here.
        raise OSError(f"paths.createDir: could not create folder: {e}")

    if not silent:
        print(f"paths.createDir: folder created: {finalDir}")
    return finalDir
