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
        "Z": {"mirrorXY": True},
    }

    # .get() with a default keeps the tool working on unexpected axis input
    kwargs = mirror_args.get(axis, {"mirrorYZ": True})
    cmds.mirrorJoint(joint, mirrorBehavior=True, searchReplace=search_replace, **kwargs)


def mirror_from_selection(axis="X", search_replace=("L_", "R_")):
    """
    Brief: Mirror the top-most joints in the current selection.

    mirrorJoint works on one joint at a time and mirrors the whole descendant
    chain, so only the top-most selected joints are mirrored — a selected
    child whose parent is also selected would otherwise be mirrored twice.

    Args:
        axis (str): Symmetry axis. Defaults to "X". Valid: "X", "Y", "Z".
        search_replace (tuple): (search, replace) pair applied to the
            mirrored names. Defaults to ("L_", "R_").

    Returns:
        None.
    """
    selected = cmds.ls(selection=True, type="joint", long=True)
    if not selected:
        cmds.warning("Select the joints")
        return

    # Only mirror the top-most selected joints: mirrorJoint duplicates the
    # joint AND its whole descendant chain, so a selected child whose
    # ancestor is also selected would be mirrored twice (duplicate copies).
    # With long names, a child path starts with the ancestor path plus "|".
    joints = [
        j for j in selected if not any(j.startswith(other + "|") for other in selected)
    ]

    mirror_args = {
        "X": {"mirrorYZ": True},
        "Y": {"mirrorXZ": True},
        "Z": {"mirrorXY": True},
    }
    kwargs = mirror_args.get(axis, {"mirrorYZ": True})

    for joint in joints:
        cmds.mirrorJoint(
            joint, mirrorBehavior=True, searchReplace=search_replace, **kwargs
        )
