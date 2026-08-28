"""
mirror_joint_tool.py
====================
Setup tool for mirroring joints across a symmetry plane.

Wraps cmds.mirrorJoint with mirrorBehavior=True so the duplicated chain keeps a
proper mirrored orientation (not the "lazy" mirror), plus search/replace naming
to flip side prefixes automatically.

Requirements:
    - Joints to mirror must have the search pattern in their name for the
      mirrored copy to rename cleanly (L_ -> R_).
    - mirrorBehavior=True requires joints with proper jointOrient.

Examples:
    >>> mirror_joint("L_arm_jnt", axis="X")
    >>> mirror_from_selection(axis="X")
"""

import maya.cmds as cmds


def mirror_joint(joint, axis="X", search_replace=("L_", "R_")):
    """
    Brief: Mirror a single joint across the given axis.

    Args:
        joint (str): Name of the joint to mirror.
        axis (str): Symmetry axis. Defaults to "X". Valid: "X", "Y", "Z".
        search_replace (tuple): (search, replace) pair applied to the
            mirrored names. Defaults to ("L_", "R_").

    Returns:
        None.
    """
    if not cmds.ls(joint):
        cmds.warning(f"Joint '{joint}' not found")
        return

    # Maya's mirror flags are planes, not axes: mirroring across X flips
    # with mirrorYZ, so each axis maps to the plane that contains the other two
    mirror_args = {
        "X": {"mirrorYZ": True},
        "Y": {"mirrorXZ": True},
        "Z": {"mirrorXY": True}
    }

    # .get() with a default keeps the tool working on unexpected axis input
    kwargs = mirror_args.get(axis, {"mirrorYZ": True})
    cmds.mirrorJoint(joint, mirrorBehavior=True, searchReplace=search_replace, **kwargs)


def mirror_from_selection(axis="X", search_replace=("L_", "R_")):
    """
    Brief: Mirror every joint in the current selection.

    mirrorJoint works on one joint at a time, so the selection is looped.

    Args:
        axis (str): Symmetry axis. Defaults to "X". Valid: "X", "Y", "Z".
        search_replace (tuple): (search, replace) pair applied to the
            mirrored names. Defaults to ("L_", "R_").

    Returns:
        None.
    """
    joints = cmds.ls()
    if not joints:
        cmds.warning("Select the joints")
        return

    mirror_args = {
        "X": {"mirrorYZ": True},
        "Y": {"mirrorXZ": True},
        "Z": {"mirrorXY": True}
    }
    kwargs = mirror_args.get(axis, {"mirrorYZ": True})

    for joint in joints:
        cmds.mirrorJoint(joint, mirrorBehavior=True, searchReplace=search_replace, **kwargs)
