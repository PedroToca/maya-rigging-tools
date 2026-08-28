"""
leg_builder.py [ARCHIVED — superseded by limb_builder.py]
=========================================================
Learning artifact: first attempt at a single-chain leg rig builder.

This was built step by step to learn the fundamentals: locators as position
sources, joint chains, offset-hierarchy controllers, and the prev_ctl FK
chaining pattern. It was later redesigned into limb_builder.py with the
production triple-chain (skin/FK/IK) architecture.

Known limitations (why it was redesigned):
    - Single joint chain: FK controls parent the deformation joints directly,
      so FK and IK fight over the same joints.
    - create_ik() is incomplete: ik_ctl / ik_Handle are never assigned, and
      the pole vector control was never added.
    - Joint names are hardcoded instead of data-driven.

Kept for reference on the learning path — do not use in production.
"""

import maya.cmds as cmds

names = ["legUp", "legLow", "ankle", "ball", "toe"]

def create_leg_locators(side="L_"):
    """
    Brief: Create one locator per leg joint, at the origin.

    Args:
        side (str): Side prefix. Defaults to "L_".

    Returns:
        None.
    """
    for name in names:
        cmds.spaceLocator(name=f"{side}{name}_loc")


def create_leg_joints(side="L_"):
    """
    Brief: Create the single leg joint chain from locator positions.

    Joints stay selected after creation, so each cmds.joint() chains under
    the previous one automatically (Maya also orients each parent to its child).

    Args:
        side (str): Side prefix. Defaults to "L_".

    Returns:
        None.
    """
    for name in names:
        jointName = f"{side}{name}_jnt"
        # Locators are parentless, so .translate equals world position
        poslist = cmds.getAttr(f"{side}{name}_loc" + ".translate")
        pos = poslist[0]
        cmds.joint(name=jointName, position=pos)
        print(cmds.listRelatives(jointName, parent=True))


def make_controller(name, side="L_"):
    """
    Brief: Create a controller with its offset hierarchy (_off/_auto/_grp/_ctl).

    Args:
        name (str): Base name without side or suffix.
        side (str): Side prefix. Defaults to "L_".

    Returns:
        tuple: (off_name, ctl_name).
    """
    controllername = (side + name)
    # circle returns [transform, shape] — [0] grabs the transform
    ctl = cmds.circle(name=controllername + "_ctl")[0]
    grp = cmds.group(name=controllername + "_grp")
    auto = cmds.group(name=controllername + "_auto")
    off = cmds.group(name=controllername + "_off")

    cmds.parent(ctl, grp)
    cmds.parent(grp, auto)
    cmds.parent(auto, off)

    return off, ctl


def make_controller_at_position(name, side="L_"):
    """
    Brief: Create a controller and place it at its locator's position.

    NOTE: unlike limb_builder.py's version, this reads the locator itself
    rather than receiving a position argument — less flexible, kept as-is.

    Args:
        name (str): Base name without side or suffix.
        side (str): Side prefix. Defaults to "L_".

    Returns:
        tuple: (off_name, ctl_name).
    """
    jointposlist = cmds.getAttr(f"{side}{name}_loc" + ".translate")
    joinpos = jointposlist[0]
    position = joinpos
    make_controller(name, side)
    off_name = side + name + "_off"
    ctl_name = side + name + "_ctl"
    # The _off absorbs the position so the _ctl stays zeroed
    cmds.xform(off_name, worldSpace=True, translation=position)
    return off_name, ctl_name


def create_fk_controls(side="L_"):
    """
    Brief: Create one FK control per joint and chain them via prev_ctl.

    Args:
        side (str): Side prefix. Defaults to "L_".

    Returns:
        None.
    """
    # Remembers the previous iteration's control — the chaining reference
    prev_ctl = None
    for name in names:
        off, ctl = make_controller_at_position(name, side)
        joint = f"{side}{name}_jnt"
        cmds.parent(joint, ctl)
        if prev_ctl:
            # Chain through the _off so the _ctl stays zeroed
            cmds.parent(off, prev_ctl)
        prev_ctl = ctl


def create_ik(side="L_"):
    """
    Brief: [INCOMPLETE] Create the IK handle and end control for the leg.

    Known bugs (left as-is, this file is a learning artifact):
        - The ikHandle return value is discarded, so the handle name is lost.
        - ik_ctl / ik_Handle are referenced but never assigned.
        - side="L" is missing the underscore, breaking the locator lookup.
        - No pole vector control or constraint.

    Args:
        side (str): Side prefix. Defaults to "L_".

    Returns:
        None.
    """
    cmds.ikHandle(
        name=f"{side}legIKHandler",
        startJoint=f"{side}legUp_jnt",
        endEffector=f"{side}ankle_jnt",
        solver="ikRPsolver"
    )
    make_controller_at_position(name="ik", side="L")
    cmds.pointConstraint(ik_ctl, ik_Handle, maintainOffset=True)
