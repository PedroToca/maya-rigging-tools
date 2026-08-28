"""
rename_hierarchy.py
===================
Setup tool for batch renaming nodes by find/replace.

Offers two modes: rename across the whole scene by pattern, or rename scoped
to a hierarchy under a given root. Useful for flipping sides (L_ -> R_) when
duplicating limbs or mirroring setups.

Requirements:
    - rename_in_hierarchy expects the root node to exist.
    - Hierarchy renames are applied child-first to avoid invalidating the
      full paths of nodes not yet processed.

Examples:
    >>> rename_by_pattern(search="L_", replace="R_")
    >>> rename_in_hierarchy(root="L_arm_GRP", search="L_", replace="R_")
"""

import maya.cmds as cmds


def rename_by_pattern(search="L_", replace="R_"):
    """
    Brief: Rename every scene node whose name contains the search pattern.

    Args:
        search (str): Substring to find. Defaults to "L_".
        replace (str): Substring to swap in. Defaults to "R_".

    Returns:
        None.
    """
    nodes = cmds.ls("*" + search + "*")
    if not nodes:
        cmds.warning("No nodes found")
        return
    for node in nodes:
        new_name = node.replace(search, replace)
        cmds.rename(node, new_name)


def rename_in_hierarchy(root, search="L_", replace="R_"):
    """
    Brief: Rename nodes containing a pattern, scoped to a hierarchy.

    ls(allDescendents=True) returns full paths with the parent first, so the
    list is iterated in reverse (children before parents). Renaming a parent
    first would invalidate the stored paths of its children.

    Args:
        root (str): Name of the hierarchy root node.
        search (str): Substring to find. Defaults to "L_".
        replace (str): Substring to swap in. Defaults to "R_".

    Returns:
        None.
    """
    if not cmds.ls(root):
        cmds.warning(f"Root '{root}' not found")
        return

    # or [] guards against ls returning None on empty result
    descendants = cmds.ls(root, allDescendents=True, type="transform") or []
    to_rename = [node for node in descendants if search in node]

    if not to_rename:
        cmds.warning(f"No '{search}' nodes in hierarchy")
        return

    # reversed(): children first, parents last — paths stay valid
    for node in reversed(to_rename):
        new_name = node.replace(search, replace)
        cmds.rename(node, new_name)
