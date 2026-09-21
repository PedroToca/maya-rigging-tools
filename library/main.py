"""
main.py
=======
Business layer of the control library: export, list, import.

WHAT: turns the current selection into library .mb files and brings
them back into any scene. One file per control - the UI builds one
button per file, so importing never drags unwanted nodes along.
Course references: M2-L09.14 (export), M2-L09.15 (get + import).

Library layout on disk (created on first export):

    <repo>/library/_control_lib/
        C_box_off.mb
        C_sphere_off.mb
        ...

The exported node is the TOP of the offset stack (the _off group), so
a library entry imports as the full _off -> ... -> _ctl hierarchy,
ready to parent under the rig root.

Two Maya limitations to keep in mind (from the course):
    - Importing a file CANNOT be undone (Ctrl+Z does not restore it).
    - Plugins that were loaded when exporting can travel inside the
      .mb as "requires" lines. If Maya complains about a missing
      plugin when opening a library file, the fix is to open it, clean
      the scene and re-export.

Usage:
    from library import main
    main.exportControl()                      # selection -> library
    main.getControllers()                     # ["C_box_off.mb", ...]
    main.importControl(["C_box_off.mb"])      # library -> scene
"""

import os

import maya.cmds as cmds

from library import files, paths

# Underscore name = internal folder of the package. The UI reads it
# too (to open it in the OS explorer), end users only touch it to
# delete files by hand.
CONTROL_DIR_NAME = "_control_lib"
FILE_TYPE = ".mb"


def control_dir():
    """
    Brief: full path of the controls folder (does NOT create it).

    Returns:
        str: <package dir>/_control_lib
    """
    return os.path.join(paths.getCurrentDir(__file__), CONTROL_DIR_NAME)


def filter_export_selection(selection=None):
    """
    Brief: split nodes into (valid, invalid) for library export.

    Valid = nodes in the world (no parent). Export Selection on a
    parented node would carry the WHOLE upper hierarchy into the .mb,
    which is exactly what a shape library must never do.

    Args:
        selection (list[str] | None): node names; None reads the
            current selection.

    Returns:
        tuple(list[str], list[str]): (valid, invalid)
    """
    sel = selection if selection is not None else (cmds.ls(selection=True) or [])
    valid, invalid = [], []
    for each in sel:
        if cmds.listRelatives(each, parent=True):
            invalid.append(each)
        else:
            valid.append(each)
    return valid, invalid


def exportControl(stopIfInvalid=True, override=False):
    """
    Brief: export the selection to the library folder, one .mb per
    node, named after the node.

    Args:
        stopIfInvalid (bool): True stops everything if any selected
            node is under a hierarchy; False exports the valid ones
            and skips the rest.
        override (bool): True deletes and re-exports files that
            already exist; False skips them (safe default - the user
            may not realize a same-name file is there).

    Returns:
        list[str]: file names written (skips not included).
    """
    valid, invalid = filter_export_selection()
    if not valid and not invalid:
        print("Control Library: select at least one object to export.")
        return []

    if invalid and stopIfInvalid:
        print(
            f"Control Library: invalid objects (under hierarchy): {', '.join(invalid)}"
        )
        print(
            "Control Library: unparent them to world, or export with "
            "stopIfInvalid=False to skip them."
        )
        return []
    if invalid:
        print(f"Control Library: skipping (under hierarchy): {', '.join(invalid)}")
    if not valid:
        print("Control Library: no valid objects to export.")
        return []

    # Resolve (or create) the controls folder next to this module.
    libDir = paths.createDir(
        path=paths.getCurrentDir(__file__), directory=CONTROL_DIR_NAME, silent=True
    )
    if not libDir:
        return []

    written = []
    for each in valid:
        # Export one node at a time - Export Selection only sees ONE
        # selection, so each file gets exactly one control stack.
        cmds.select(each, noExpand=True)
        fileName = each + FILE_TYPE
        if files.fileAlreadyExists(filePath=libDir, fileName=fileName):
            if override:
                fullPath = os.path.join(libDir, fileName)
                print(f"Control Library: overwriting {fullPath}")
                os.remove(fullPath)
                files.exportSelection(filePath=libDir, fileName=fileName)
                written.append(fileName)
            else:
                print(
                    f"Control Library: skipping existing file {fileName} "
                    "(override=True to replace)"
                )
        else:
            files.exportSelection(filePath=libDir, fileName=fileName)
            written.append(fileName)

    # Restore a clean selection state after the per-node select loop.
    cmds.select(clear=True)
    print(f"Control Library: exported {len(written)} control(s): {', '.join(written)}")
    return written


def getControllers():
    """
    Brief: all library files ready to import.

    Returns:
        list[str]: .mb file names. Empty if the folder does not exist
        yet or holds nothing - the UI is born without buttons and
        that is fine.
    """
    fullDir = control_dir()
    if not os.path.exists(fullDir):
        return []
    return files.listFiles(fullDir, types=FILE_TYPE)


def importControl(controllers=None):
    """
    Brief: import the given library files into the scene.

    WARNING: importing cannot be undone - Ctrl+Z does not restore it.
    Duplicate manually-imported stacks instead of relying on undo.

    Each file imports into its own namespace (named after the file) so
    a node with the same name never clashes with scene nodes. When the
    root namespace is free, the namespace is merged away and the nodes
    come in with clean names; on a real clash the nodes keep the
    namespace prefix (e.g. "C_box_off:C_box_off") instead of failing.

    Args:
        controllers (list[str]): file names WITH extension, e.g.
            ["C_box_off.mb"]. Use a list even for a single control.

    Returns:
        int: number of files imported.
    """
    controllers = controllers or []
    if not controllers:
        print("Control Library: no controllers given to importControl.")
        return 0

    controlDirFull = control_dir()
    available = getControllers()
    imported = 0
    for control in controllers:
        if control not in available:
            print(f"Control Library: not in library, skipped: {control}")
            continue

        # "C_box_off.mb" -> "C_box_off" - the namespace needs the name
        # WITHOUT extension.
        name = control.replace(FILE_TYPE, "")
        fullPath = os.path.join(controlDirFull, control)
        print(f"Control Library: importing {name} from {fullPath}")

        try:
            cmds.file(fullPath, i=True, namespace=name, returnNewNodes=True)
        except Exception as e:
            # One bad file must not kill the rest of the batch.
            print(f"Control Library: FAILED {control}: {e}")
            continue

        # Merge the namespace into root for clean names. If the scene
        # already owns one of these names, the merge fails and nodes
        # simply stay namespaced - that is the graceful fallback.
        try:
            cmds.namespace(removeNamespace=":" + name, mergeNamespaceWithRoot=True)
        except RuntimeError:
            print(f"Control Library: name clash kept nodes under namespace ':{name}'")

        imported += 1
        print(f"Control Library: done\t{control}")

    return imported
