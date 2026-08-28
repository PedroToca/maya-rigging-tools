"""
unparented_controls.py
======================
QC tool for detecting controllers outside the expected rig hierarchy.

Every controller should live under the rig's top-level group (default: "RIG").
A controller parented elsewhere (or floating at world level) will not follow
the rig when it is moved, referenced, or scaled.

Requirements:
    - Controllers must follow the naming convention: <prefix>_<name>_ctl
    - The rig must have a top-level group that owns every controller.

Examples:
    >>> check_hierarchy(expected_parent="RIG")
    Controllers with not expeted parent (1):
      - L_arm_ctl
"""

import maya.cmds as cmds


def check_hierarchy(expected_parent="RIG"):
    """
    Brief: Find controllers whose top-level ancestor is not the expected parent.

    For each controller, walks up the hierarchy (parent by parent) until it
    reaches a node with no parent, then compares it against expected_parent.

    Args:
        expected_parent (str): Name of the rig's top-level group. Defaults to "RIG".

    Returns:
        None. Delegates reporting to show_report().
    """
    selection = cmds.ls("*_ctl")
    if not selection:
        cmds.warning("No Controllers to select")
        return
    violations = []
    for item in selection:
        current = item
        # Walk up until we reach the top of the hierarchy
        while True:
            parent = cmds.listRelatives(current, parent=True)
            if not parent:
                break
            current = parent[0]
        if current != expected_parent:
            violations.append(item)
    show_report(violations)


def show_report(violations):
    """
    Brief: Print a report of controllers with an unexpected hierarchy parent.

    Args:
        violations (list): Controller names flagged by check_hierarchy().

    Returns:
        None. Prints a formatted report to the console.
    """
    count = len(violations)
    header = f"Controllers with not expeted parent ({count}):"
    items = ""
    for item in violations:
        items += f"\n  - {item}"
    print(header + items)
