"""
select_controllers.py
=====================
QC tool for selecting rig controllers by convention.

Provides utilities to select all controllers, filter by side prefix (L_, R_, C_),
select only visible controllers from the current selection, and clear selection.

Requirements:
    - Controllers must follow the naming convention: <prefix>_<name>_ctl
    - Side prefixes: L_, R_, C_

Examples:
    >>> select_all()
    >>> select_side(side="R_")
    >>> select_only_visible()
    >>> deselect_all()
"""

import maya.cmds as cmds


def select_all():
    """
    Brief: Select every controller in the scene.

    Uses the *_ctl wildcard to find all controls following the naming convention.

    Returns:
        None. Prints the count of selected controllers.
    """
    selection = cmds.ls("*_ctl")
    if not selection:
        cmds.warning("No Controllers to select")
        return
    cmds.select(selection)
    count = len(selection)
    print(f"Controllers ({count}) have been selected")


def select_side(side="L_"):
    """
    Brief: Select all controllers matching a side prefix.

    Args:
        side (str): Side prefix to filter by. Defaults to "L_".
            Expected values: "L_", "R_", "C_".

    Returns:
        None. Prints the count of selected controllers.
    """
    selection = cmds.ls(side + "*_ctl")
    if not selection:
        cmds.warning(f"No controllers found for {side}")
        return
    cmds.select(selection)
    count = len(selection)
    print(f"Controllers ({count}) have been selected")


def select_only_visible():
    """
    Brief: Filter the current selection to keep only visible controllers.

    Iterates the current selection and removes controls whose visibility
    attribute is False. Useful when working in complex rigs with hidden controls.

    Returns:
        None. Prints the count of selected controllers.
    """
    selected = cmds.ls(sl=True)
    selection = []
    for each in selected:
        if cmds.getAttr(each + ".visibility"):
            selection.append(each)
    if not selection:
        cmds.warning("No Controllers to select")
        return
    cmds.select(selection)
    count = len(selection)
    print(f"Controllers ({count}) have been selected")


def deselect_all():
    """
    Brief: Clear the current selection.
    """
    cmds.select(clear=True)
    print("Selection cleared")
