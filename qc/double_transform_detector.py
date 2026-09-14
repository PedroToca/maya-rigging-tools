"""
double_transform_detector.py
============================
QC tool for detecting double transforms in a hierarchy.

A double transform happens when a node AND its parent both carry transform
values. The child's movement gets compounded by the parent's movement, so the
node appears to move twice as far as intended. In a clean rig, only one node
in a parent/child pair should hold values.

Requirements:
    - Scans all transform nodes in the scene (no naming convention needed).
    - Uses has_transform() as a reusable single-node query.

Examples:
    >>> check_double_transforms()
    L_arm_GRP and L_arm_ctl have transformations
"""

import maya.cmds as cmds


def has_transform(node, tolerance=0.001):
    """
    Brief: Check if a single node has translate or rotate values.

    Reusable helper — other QC tools can import and reuse this query.

    Args:
        node (str): Name of the node to check.
        tolerance (float): Maximum absolute value considered as zero.
            Defaults to 0.001.

    Returns:
        bool: True if the node has any translate OR rotate value above tolerance.
    """
    # getAttr on compound attrs returns [(x, y, z)] — [0] grabs the tuple
    rotations = cmds.getAttr(node + ".rotate")[0]
    rot = False
    for rot_val in rotations:
        if abs(rot_val) > tolerance:
            rot = True
    trans = False
    translation = cmds.getAttr(node + ".translate")[0]
    for trans_val in translation:
        if abs(trans_val) > tolerance:
            trans = True

    # "has transform" = either flag is True — or fuses both answers into one
    return trans or rot


def check_double_transforms(tolerance=0.001):
    """
    Brief: Find node/parent pairs where BOTH carry transform values.

    Iterates all transform nodes. For each node with transforms, queries its
    parent; if the parent also has transforms, both are reported.

    Args:
        tolerance (float): Passed through to has_transform(). Defaults to 0.001.

    Returns:
        None. Prints each parent/child pair detected.
    """
    node = cmds.ls(type="transform")
    for item in node:
        if has_transform(item):
            # or [] protects against listRelatives returning None (world roots)
            parent = cmds.listRelatives(item, parent=True) or []
            if not parent:
                continue
            padre = parent[0]
            if has_transform(padre):
                print(f"{padre} and {item} have transformations")
