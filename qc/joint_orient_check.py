"""
joint_orient_check.py
=====================
QC tool for detecting joints with rotation baked into .rotate instead of .jointOrient.

In a clean deformation skeleton, orientation lives in the jointOrient attribute
and .rotate stays at zero. Rotation values in .rotate get added on top of the
bind pose and can break skinning behavior.

Requirements:
    - No naming convention required: scans all joints by type.
    - Uses dag=True to exclude invalid DG nodes returned by type queries in Maya 2024+.

Examples:
    >>> check_joint_orient(tolerance=0.001)
    'L_arm_jnt' have trasformation
"""

import maya.cmds as cmds


def check_joint_orient(tolerance=0.001):
    """
    Brief: Find joints with non-zero rotation values in .rotate.

    Args:
        tolerance (float): Maximum absolute value considered as zero.
            Defaults to 0.001. Floats rarely compare cleanly to exactly 0.

    Returns:
        None. Prints each offending joint with its rotation values.
    """
    joints = cmds.ls(type="joint", dag=True)
    if not joints:
        cmds.warning("No joint in the scene")
        return

    for item in joints:
        # getAttr on .rotate returns a tuple (x, y, z) — iterate each axis
        trans = cmds.getAttr(item + ".rotate")
        for valor in trans:
            # abs() so negative rotations are flagged too (-3 IS a rotation)
            if abs(valor) > tolerance:
                print(f"'{item}' have trasformation")
