"""
naming_validator.py
===================
QC tool for validating controller naming conventions.

Checks that every controller in the scene follows the L_, R_, C_ prefix convention.
Reports any controllers with invalid or missing prefixes.

Requirements:
    - Controllers must follow the naming convention: <prefix>_<name>_ctl
    - Valid prefixes: L_, R_, C_

Examples:
    >>> check_controllers()
    All controlers named correctly
"""

import maya.cmds as cmds


def check_controllers():
    """
    Brief: Validate that all controllers in the scene use a valid side prefix.

    Scans for *_ctl nodes and checks if each name starts with L_, R_, or C_.
    Controllers that fail the check are passed to check_all() for reporting.

    Returns:
        list: Controllers with invalid naming. Empty list if all are valid.
    """
    selection = cmds.ls("*_ctl")
    if not selection:
        cmds.warning("No controllers found")
        return []
    controllersList = []
    for item in selection:
        # startswith accepts a tuple — returns True if the name starts with ANY of them
        if not item.startswith(("L_", "R_", "C_")):
            controllersList.append(item)
    if not controllersList:
        print("All controlers named correctly")
    else:
        check_all(controllersList)


def check_all(controllersList):
    """
    Brief: Print a report of controllers with invalid naming.

    Args:
        controllersList (list): Controller names that failed validation.

    Returns:
        None. Prints a formatted report to the console.
    """
    count = len(controllersList)
    header = f"Controllers with invalid naming ({count}):"
    items = ""
    for item in controllersList:
        items += f"\n  - {item}"
    print(header + items)
