"""
zero_transform_check.py
=======================
QC tool for detecting controllers with non-zero transforms.

A controller at rest should have translate and rotate values at zero. Non-zero
values indicate the control was moved but not zeroed out, which can cause issues
when animating or when the rig is reset.

Requirements:
    - Controllers must follow the naming convention: <prefix>_<name>_ctl
    - Float comparison uses a tolerance to avoid false positives from precision errors.

Examples:
    >>> check_zero_transforms()
    Controllers with transforms (2):
      - L_arm_ctl
      - R_leg_ctl
"""

import maya.cmds as cmds


def check_zero_transforms():
    """
    Brief: Find controllers with non-zero translate or rotate values.

    Iterates all *_ctl nodes and checks their .translate and .rotate attributes.
    A control is flagged if any axis value exceeds the tolerance.

    Returns:
        list: Controller names with non-zero transforms. Empty if all are clean.
    """
    selection = cmds.ls("*_ctl")
    if not selection:
        cmds.warning("No Controllers to select")
        return
    violation = []
    for item in selection:
        is_violation = False
        translationlist = cmds.getAttr(item + ".translate")
        rotationlist = cmds.getAttr(item + ".rotate")
        for transform in translationlist:
            if abs(transform) > 0.001:
                is_violation = True
                break
        for transform in rotationlist:
            if abs(transform) > 0.001:
                is_violation = True
                break
        if is_violation:
            violation.append(item)
    show_report(violation)
    return violation


def show_report(violation):
    """
    Brief: Print a report of controllers with non-zero transforms.

    Args:
        violation (list): Controller names flagged by check_zero_transforms.

    Returns:
        None. Prints a formatted report to the console.
    """
    count = len(violation)
    header = f"Controllers with transforms ({count}):"
    items = ""
    for item in violation:
        items += f"\n  - {item}"
    print(header + items)
