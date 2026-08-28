"""
constraint_assistant.py
=======================
Setup tool for creating constraints from names or the current selection.

Builds any *Constraint command dynamically via getattr, so one function covers
parent, point, orient, aim, and poleVector constraints. Selection order follows
Maya convention: driver first, driven second.

Requirements:
    - constraint_type must match an existing cmds command (e.g. "parent"
      resolves to cmds.parentConstraint).
    - All constraints are created with maintainOffset=True to avoid the driven
      snapping to the driver's transform.

Examples:
    >>> create_constraint(constraint_type="parent", driver="L_arm_ctl", driven="L_arm_jnt")
    >>> constraint_from_selection(constraint_type="point")
"""

import maya.cmds as cmds


def create_constraint(constraint_type="parent", driver="", driven=""):
    """
    Brief: Create a constraint between two named nodes.

    Args:
        constraint_type (str): Constraint kind, without the "Constraint" suffix.
            Defaults to "parent". Valid: parent, point, orient, aim, poleVector...
        driver (str): Node that drives the target.
        driven (str): Node that follows the driver.

    Returns:
        None.
    """
    if not cmds.ls(driver, driven):
        cmds.warning("Select de driven/driver controllers")
        return
    # getattr resolves a string into the actual function on the cmds module
    constraint_func = getattr(cmds, constraint_type + "constraint")
    constraint_func(driver, driven, maintainOffset=True)


def constraint_from_selection(constraint_type="parent"):
    """
    Brief: Create a constraint from the current selection (2+ nodes).

    Selection order matters: first selected = driver, second = driven.
    Extra selected nodes beyond the first two are ignored.

    Args:
        constraint_type (str): Constraint kind, without the "Constraint" suffix.
            Defaults to "parent".

    Returns:
        None.
    """
    selection = cmds.ls()
    if not selection:
        cmds.warning("Select de driven/driver controllers")
        return

    constraint_func = getattr(cmds, constraint_type + "constraint")
    constraint_func(selection[0], selection[1], maintainOffset=True)
