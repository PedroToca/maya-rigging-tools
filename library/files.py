"""
files.py
========
File-system layer of the control library: list, check, export.

WHAT: list the files of a folder (optional extension filter), check if
a file name already exists there, and export the current selection to
a .mb file. Course reference: M2-L09.13 (Libreria de controles II).

The three functions share the course rhythm: documented kwargs ->
validate inputs (raise) -> do the work. They raise instead of warning
because this layer runs under main.py / gui.py, which catch and report
to the user.

Why export to .mb (Maya Binary): same format the course uses, smaller
and faster to read than .ma, and the UI lists files by that extension.
"""

import os

import maya.cmds as cmds


def listFiles(filePath="", types=""):
    """
    Brief: every FILE inside the directory (folders are skipped).

    Args:
        filePath (str): directory to analyze.
        types (str): extension filter, e.g. ".mb". Empty returns all.

    Returns:
        list[str]: file names (no path prefix). Empty if none match.

    Raises:
        OSError: empty filePath, or filePath does not exist.
    """
    if not filePath:
        raise OSError("files.listFiles: you must pass a path.")
    if not os.path.exists(filePath):
        raise OSError(f"files.listFiles: path does not exist: {filePath}")

    result = []
    for each in os.listdir(filePath):
        thisPath = os.path.join(filePath, each)
        if os.path.isfile(thisPath):
            # Filter by extension only when one was requested. The
            # check is substring-based (".mb" in name), matching the
            # course implementation - good enough for this folder.
            if types:
                if types in each:
                    result.append(each)
            else:
                result.append(each)
    return result


def fileAlreadyExists(filePath="", fileName=""):
    """
    Brief: True if a file with that exact name lives in that folder.

    Args:
        filePath (str): directory to analyze.
        fileName (str): file name to look for.

    Returns:
        bool

    Raises:
        OSError: empty inputs, or filePath does not exist.
    """
    if not filePath:
        raise OSError("files.fileAlreadyExists: you must pass a path.")
    if not fileName:
        raise OSError("files.fileAlreadyExists: you must pass a file name.")
    if not os.path.exists(filePath):
        raise OSError(f"files.fileAlreadyExists: path does not exist: {filePath}")

    return fileName in os.listdir(filePath)


def exportSelection(filePath="", fileName=""):
    """
    Brief: export the current selection to <filePath>/<fileName> as
    Maya Binary. Only runs if the file does NOT exist yet - the caller
    (main.exportControl) decides what to do with collisions.

    Args:
        filePath (str): destination directory.
        fileName (str): destination file name, e.g. "C_box_off.mb".

    Raises:
        ValueError: a file with that name already exists.
        RuntimeError: cmds.file failed (it can fail in several ways,
            not only OSError - course note from M2-L09.13).
    """
    if not filePath:
        raise OSError("files.exportSelection: you must pass a path.")
    if not fileName:
        raise OSError("files.exportSelection: you must pass a file name.")
    if fileAlreadyExists(filePath=filePath, fileName=fileName):
        raise ValueError(f"files.exportSelection: file already exists: {fileName}")

    # Remember the selection: exporting switches it, and a tool that
    # eats the user's selection is a tool nobody trusts twice.
    previousSel = cmds.ls(selection=True) or []
    try:
        # Flag values mirror Maya's Export Selection options.
        # exportSelected - exact spelling, the missing-t typo from the
        # course video is the classic silent killer here.
        cmds.file(
            os.path.join(filePath, fileName),
            exportSelected=True,
            type="mayaBinary",
            force=True,
        )
    except Exception as e:
        # Broad catch on purpose: cmds.file raises mixed exception
        # types (M2-L09.13) - re-raised as RuntimeError with context.
        raise RuntimeError(f"files.exportSelection: error exporting {fileName}: {e}")
    finally:
        if previousSel:
            cmds.select(previousSel, noExpand=True)
