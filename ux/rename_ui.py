"""rename_ui - Batch rename tool with preview window.

WHAT: A cmds window that renames many nodes at once. Modes: find/replace,
add prefix, add suffix, renumber (base + counter). Scopes: selection,
hierarchy under a root, or whole scene. Always PREVIEW before writing.

WHY PREVIEW: this is a write tool (Fase 2 logic) driven by a UI (Fase 4
patterns) - the dry_run exercise of lesson 02.2 turned into a window, so
you LOOK at what would happen before letting it touch the scene.

Usage (Script Editor):
    from ux.rename_ui import open_rename_window
    open_rename_window()

Course references: 02.2 rename_hierarchy (type="transform", child->parent
order, rename returning the REAL final name), Soluciones Fase 2 (dry_run,
prefix, counter), 04.1 Windows y layouts (5-step window pattern),
04.2 Widgets (capture IDs, query mode, nested callbacks).
"""

import maya.cmds as cmds

WINDOW_NAME = "ptRenameWin"

# UI label -> (needs_find, needs_replace, needs_prefix, needs_suffix, needs_base)
# One dict describes which fields each mode consumes - the UI shows all
# fields and this map documents (and guards) the relevant ones.
MODE_FIELDS = {
    "Find / Replace": ("find", "replace", "", "", ""),
    "Add Prefix": ("", "", "prefix", "", ""),
    "Add Suffix": ("", "", "", "suffix", ""),
    "Numbering": ("", "", "", "", "base"),
}

# UI label -> internal scope key. The SIDE_MAP pattern of lesson 04.2:
# the UI speaks human ("Whole Scene"), the logic speaks keys ("scene"),
# and this dict is the ONLY bridge - labels are never compared in logic.
SCOPE_MAP = {
    "Selection": "selection",
    "Hierarchy": "hierarchy",
    "Whole Scene": "scene",
}


# ---------------------------------------------------------------------------
# Logic - plain functions, testable without opening the window
# ---------------------------------------------------------------------------


def collect_targets(scope="selection", root=""):
    """Long paths of nodes a rename would consider, parent-first order.

    type="transform" keeps shapes out (renaming a transform renames its
    shape - listing both is the classic mid-tool crash of lesson 02.2).
    """
    if scope == "selection":
        return cmds.ls(selection=True, long=True, type="transform") or []
    if scope == "hierarchy":
        if not cmds.objExists(root):
            cmds.warning("rename_ui: root '%s' not found" % root)
            return []
        # ls() has NO allDescendents flag (TypeError in Maya 2027) -
        # listRelatives is the canonical hierarchy walk. fullPath=True
        # returns |root|...|node paths, same shape ls would give.
        return (
            cmds.listRelatives(
                root, allDescendents=True, fullPath=True, type="transform"
            )
            or []
        )
    if scope == "scene":
        return cmds.ls(long=True, type="transform") or []
    # Unknown scope = a bug in the UI/logic bridge. Fail LOUD and empty -
    # never fall through to "whole scene" (that silent fallback renamed
    # the user's entire scene when scope labels mismatched).
    cmds.warning("rename_ui: unknown scope '%s'" % scope)
    return []


def compute_renames(
    nodes, mode, find="", replace="", prefix="", suffix="", base="", padding=2
):
    """Plan renames without touching the scene. Returns list of tuples.

    Each tuple: (long_path, current_short, new_short, warning_or_empty).
    Nodes whose name would NOT change are left out - the plan only
    contains real work, so the preview never lies with filler lines.
    """
    plan = []
    if mode == "Numbering":
        for i, path in enumerate(nodes, start=1):
            short = path.split("|")[-1]
            new_short = "%s%0*d" % (base, padding, i)
            if new_short != short:
                plan.append((path, short, new_short, ""))
        return plan

    for path in nodes:
        short = path.split("|")[-1]
        if mode == "Find / Replace":
            if not find or find not in short:
                continue
            new_short = short.replace(find, replace)
        elif mode == "Add Prefix":
            if not prefix:
                continue
            new_short = prefix + short
        else:  # Add Suffix
            if not suffix:
                continue
            new_short = short + suffix
        if new_short == short:
            continue
        # Collision check: a DIFFERENT node already owns the target name -
        # rename would not fail, Maya silently numbers it (lesson 02.2).
        warning = ""
        if cmds.objExists(new_short):
            warning = "name already exists - Maya will number it"
        plan.append((path, short, new_short, warning))
    return plan


def apply_renames(plan):
    """Execute a plan: DEEPEST nodes first, one undo chunk for all.

    Depth order is the generalized reversed() of lesson 02.2: renaming a
    parent invalidates every stored path below it, so children go first.
    undoInfo chunk = one Ctrl+Z undoes the whole batch.

    On rigged/skinned scenes each rename has real cost: Maya re-wires
    every dependency that references the node (constraints, skinCluster,
    driven keys...). Two courtesies keep the wait visible and shorter:
    progressWindow reports batch position, refresh(suspend=True) skips
    viewport redraws between renames. Both restored in finally, ALWAYS.
    """
    ordered = sorted(plan, key=lambda item: item[0].count("|"), reverse=True)
    numbered = []
    total = len(ordered)
    cmds.progressWindow(
        title="Batch Rename",
        progress=0,
        maxValue=total,
        status="Renaming 0/%d" % total,
        isInterruptable=False,
    )
    cmds.refresh(suspend=True)
    cmds.undoInfo(openChunk=True, chunkName="renameUI")
    try:
        for i, (path, _short, new_short, _warn) in enumerate(ordered, start=1):
            cmds.progressWindow(
                edit=True, progress=i, status="Renaming %d/%d" % (i, total)
            )
            # rename returns the REAL final name - if Maya had to number
            # it, we report instead of failing silently.
            actual = cmds.rename(path, new_short)
            if actual != new_short:
                numbered.append((new_short, actual))
    finally:
        cmds.undoInfo(closeChunk=True)
        cmds.refresh(suspend=False)
        cmds.refresh(cv=True)  # one clean redraw after the batch
        cmds.progressWindow(endProgress=True)
    return numbered


# ---------------------------------------------------------------------------
# UI - 5-step window pattern (exists -> delete -> create -> fill -> show)
# ---------------------------------------------------------------------------


def open_rename_window():
    """Open the batch rename window (idempotent - safe to call twice)."""
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)

    # No fixed widthHeight: the window auto-sizes to its content, so the
    # bottom buttons can never be clipped by a wrong pixel budget.
    win = cmds.window(WINDOW_NAME, title="Batch Rename", sizeable=True)
    # scrollLayout safety net: if the user shrinks the window below the
    # content height, a scrollbar appears instead of hiding the buttons.
    cmds.scrollLayout(horizontalScrollBarThickness=0)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6)

    cmds.text(label="Batch Rename", font="boldLabelFont")
    cmds.separator(height=8, style="in")

    mode_menu = cmds.optionMenuGrp(label="Mode")
    for label in MODE_FIELDS:
        cmds.menuItem(label=label)

    scope_menu = cmds.optionMenuGrp(label="Scope")
    for label in SCOPE_MAP:
        cmds.menuItem(label=label)

    root_field = cmds.textFieldGrp(label="Root (hierarchy)", text="")

    cmds.separator(height=8, style="in")
    find_field = cmds.textFieldGrp(label="Find", text="L_")
    replace_field = cmds.textFieldGrp(label="Replace", text="R_")
    prefix_field = cmds.textFieldGrp(label="Prefix", text="SKEL_")
    suffix_field = cmds.textFieldGrp(label="Suffix", text="_ctl")
    base_field = cmds.textFieldGrp(label="Base name", text="ctrl")
    pad_slider = cmds.intSliderGrp(
        label="Padding", field=True, minValue=1, maxValue=4, value=2
    )

    cmds.separator(height=8, style="in")
    cmds.text(
        label="Preview (only nodes that change):", align="left", font="boldLabelFont"
    )
    preview_list = cmds.textScrollList(height=170, allowMultiSelection=False)
    info_text = cmds.text(label="No preview yet - press Preview.", align="left")

    # The plan lives here so Preview (compute) and Rename (apply) share it
    # without globals - the nested-scope pattern of lesson 04.2.
    planned = []

    def _read_settings():
        return {
            "mode": cmds.optionMenuGrp(mode_menu, query=True, value=True),
            # Translate UI label -> internal key at the ONE crossing point.
            "scope": SCOPE_MAP[cmds.optionMenuGrp(scope_menu, query=True, value=True)],
            "root": cmds.textFieldGrp(root_field, query=True, text=True),
            "find": cmds.textFieldGrp(find_field, query=True, text=True),
            "replace": cmds.textFieldGrp(replace_field, query=True, text=True),
            "prefix": cmds.textFieldGrp(prefix_field, query=True, text=True),
            "suffix": cmds.textFieldGrp(suffix_field, query=True, text=True),
            "base": cmds.textFieldGrp(base_field, query=True, text=True),
            "padding": cmds.intSliderGrp(pad_slider, query=True, value=True),
        }

    def _build_plan():
        """Read widgets -> collect targets -> compute plan. Returns list."""
        settings = _read_settings()

        if settings["scope"] == "selection" and not cmds.ls(selection=True):
            cmds.warning("rename_ui: nothing selected")
            return []
        if settings["scope"] == "hierarchy" and not settings["root"]:
            cmds.warning("rename_ui: hierarchy scope needs a root")
            return []
        if settings["mode"] == "Find / Replace" and not settings["find"]:
            cmds.warning("rename_ui: Find / Replace needs a Find text")
            return []
        if settings["mode"] == "Numbering" and not settings["base"]:
            cmds.warning("rename_ui: Numbering needs a base name")
            return []

        targets = collect_targets(settings["scope"], settings["root"])
        return compute_renames(
            targets,
            settings["mode"],
            find=settings["find"],
            replace=settings["replace"],
            prefix=settings["prefix"],
            suffix=settings["suffix"],
            base=settings["base"],
            padding=settings["padding"],
        )

    def do_preview(_):
        planned[:] = _build_plan()
        cmds.textScrollList(preview_list, edit=True, removeAll=True)
        cmds.textScrollList(
            preview_list,
            edit=True,
            append=[
                "%s -> %s%s" % (short, new, ("  [%s]" % warn) if warn else "")
                for _path, short, new, warn in planned
            ],
        )
        info = "%d node(s) would be renamed." % len(planned)
        if any(warn for _p, _s, _n, warn in planned):
            info += " Items in brackets will collide."
        cmds.text(info_text, edit=True, label=info)

    def do_rename(_):
        if not planned:
            do_preview(_)
        if not planned:
            return
        answer = cmds.confirmDialog(
            title="Batch Rename",
            message="Rename %d node(s)? One Ctrl+Z undoes all." % len(planned),
            button=["Rename", "Cancel"],
            defaultButton="Rename",
            cancelButton="Cancel",
            dismissString="Cancel",
        )
        if answer != "Rename":
            return
        numbered = apply_renames(planned)
        cmds.textScrollList(preview_list, edit=True, removeAll=True)
        cmds.text(
            info_text,
            edit=True,
            label="Renamed %d node(s). Collisions numbered: %d"
            % (len(planned), len(numbered)),
        )
        for wanted, actual in numbered:
            cmds.warning("rename_ui: wanted '%s', Maya gave '%s'" % (wanted, actual))
        planned[:] = []

    cmds.rowLayout(numberOfColumns=3, columnWidth3=(130, 130, 130))
    cmds.button(label="Preview", height=36, command=do_preview)
    cmds.button(label="Rename", height=36, command=do_rename)
    cmds.button(
        label="Close",
        height=36,
        command=lambda x: cmds.deleteUI(WINDOW_NAME, window=True),
    )
    cmds.setParent("..")

    cmds.showWindow(win)
