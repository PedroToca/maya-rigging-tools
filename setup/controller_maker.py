"""
controller_maker.py
===================
Setup tool for creating controllers with the standard offset hierarchy.

Every controller is created with a 4-level offset hierarchy:

    _off  -> holds world position and receives parenting (the "coaster")
    _auto -> reserved for secondary constraints / auto-parenting
    _grp  -> extra clean-up level (freeze transforms)
    _ctl  -> the node the animator touches, always zeroed at rest

The offset groups absorb position and parenting so the _ctl itself keeps its
transforms at zero. Zeroing out a control then reliably returns it to rest.

Requirements:
    - Naming convention: <side><name>_ctl, e.g. L_arm_ctl

Examples:
    >>> make_controller("arm")
    >>> make_controller_at_position("arm", side="L_", position=(5, 10, 0))
"""

import maya.cmds as cmds


def make_controller(name, side="L_"):
    """
    Brief: Create a controller with its offset hierarchy at the origin.

    Args:
        name (str): Base name of the controller (without side or suffix).
        side (str): Side prefix. Defaults to "L_". Expected: "L_", "R_", "C_".

    Returns:
        tuple(str, str): (_off, _ctl) node names, so callers can keep
        references instead of guessing names back from the scene.
    """
    controllername = (side + name)
    # circle returns [transform, shape] — [0] grabs the transform we parent
    ctl = cmds.circle(name=controllername + "_ctl")[0]
    grp = cmds.group(name=controllername + "_grp")
    auto = cmds.group(name=controllername + "_auto")
    off = cmds.group(name=controllername + "_off")

    cmds.parent(ctl, grp)
    cmds.parent(grp, auto)
    cmds.parent(auto, off)

    cmds.makeIdentity(ctl, apply=True, t=True, r=True, s=True)
    return off, ctl


def make_controller_at_position(name, side="L_", position=(0, 0, 0)):
    """
    Brief: Create a controller and place it at a world-space position.

    The position is applied to the _off group, NOT the _ctl, so the control
    itself stays zeroed at its new location.

    Args:
        name (str): Base name of the controller (without side or suffix).
        side (str): Side prefix. Defaults to "L_".
        position (tuple): World-space (x, y, z) position. Defaults to origin.

    Returns:
        tuple(str, str): (_off, _ctl) node names.
    """
    off, ctl = make_controller(name, side)
    cmds.xform(off, worldSpace=True, translation=position)
    return off, ctl
