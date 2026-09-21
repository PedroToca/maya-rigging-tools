"""
pt_rigtools_shelf.py - Auto-built Maya shelf for PedroToca/maya-rigging-tools.

WHAT: Creates (and keeps) a "PT_RigTools" shelf tab in Maya with one button
per tool of the maya-rigging-tools repository (QC validators, setup tools,
rig builders, control library). Called at startup from userSetup.mel via:

    evalDeferred "python(\"import pt_rigtools_shelf; "
                 "pt_rigtools_shelf.ensure_shelf()\")";

CANONICAL COPY vs INSTALLED COPY: this file is versioned at
<repo>/shelf/pt_rigtools_shelf.py. To install, copy it into
<Documents>/maya/<version>/scripts/ and make sure REPO_PATH below still
points at the cloned repo (edit it if the clone lives elsewhere).

WHY AUTO-BUILT: the shelf is generated from code, not saved as a prefs file.
If Maya's prefs are reset, or the repo gets new tools, the shelf rebuilds
itself from this single source of truth. The repo is never copied into
Maya's scripts dir - buttons import directly from REPO_PATH, so a
`git pull` instantly updates the tools.

USAGE:
    - Automatic: starts with Maya (see userSetup.mel).
    - Manual rebuild (also after editing this file, same session - the
      reload is REQUIRED, a plain import reuses the cached module):
        import importlib, pt_rigtools_shelf
        importlib.reload(pt_rigtools_shelf)
        pt_rigtools_shelf.ensure_shelf(rebuild=True)

REQUIRES: Maya 2025+ (embedded Python 3.11), repo cloned at REPO_PATH.
"""

import importlib
import os
import sys

# Root of the tools repository. The repo has no __init__.py files: its
# packages (qc/, setup/, builders/, library/, ux/) are namespace packages
# resolved by putting this path on sys.path. IMPORTANT: only correct in the
# installed copy - if this file moved, point it at your clone again.
REPO_PATH = r"C:\Trabajo_OpenCode\maya-rigging-tools"

SHELF_NAME = "PT_RigTools"


# ---------------------------------------------------------------------------
# Repo import helper
# ---------------------------------------------------------------------------


def _ensure_repo_on_path():
    """Add the repo root to sys.path once, so `import qc...` resolves."""
    if REPO_PATH not in sys.path:
        sys.path.append(REPO_PATH)


def _call(module_name, func_name, **kwargs):
    """Import a tool module fresh from the repo and call one function.

    importlib.import_module reuses the cached module within a session;
    restart Maya (or rebuild the shelf) after `git pull`ing the repo.
    """
    _ensure_repo_on_path()
    func = getattr(importlib.import_module(module_name), func_name)
    return func(**kwargs)


# ---------------------------------------------------------------------------
# Interactive wrappers (tools that need arguments get a small dialog)
# ---------------------------------------------------------------------------


def _prompt_make_controller():
    """controller_maker.make_controller() needs a name: ask for it.

    Prompt format is 'name side' (e.g. 'arm L_'). Side defaults to 'C_'
    so a bare name still follows the L_/R_/C_ naming convention.
    """
    import maya.cmds as cmds

    result = cmds.promptDialog(
        title="Make Controller",
        message="Name and side (e.g. 'arm L_'):",
        text="arm L_",
        button="Create",
    )
    if result != "Create":
        return
    parts = cmds.promptDialog(query=True, text=True).split()
    name = parts[0] if parts else "new"
    side = parts[1] if len(parts) > 1 else "C_"
    _call("setup.controller_maker", "make_controller", name=name, side=side)


def _build_limb_dialog():
    """Small options window for limb_builder.build_limb(side, limb).

    The limb builder is TWO-PASS by design: run 1 creates locators you
    position in the viewport; you then delete that pass and run again to
    build the rig at those positions. The reminder is shown in-view.
    """
    import maya.cmds as cmds

    win = "ptLimbDialog"
    if cmds.window(win, exists=True):
        cmds.deleteUI(win)
    cmds.window(win, title="Build Limb", widthHeight=(240, 160))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=8, columnOffset=("both", 12))

    side_menu = cmds.optionMenu(label="Side")
    for item in ("L_", "R_"):
        cmds.menuItem(label=item)
    limb_menu = cmds.optionMenu(label="Limb")
    for item in ("leg", "arm"):
        cmds.menuItem(label=item)

    def _run(_):
        side = cmds.optionMenu(side_menu, query=True, value=True)
        limb = cmds.optionMenu(limb_menu, query=True, value=True)
        cmds.deleteUI(win)
        cmds.inViewMessage(
            assist="Two-pass: position locators, delete pass 1, run again.",
            position="topCenter",
            fadeOut=True,
            fadeInTime=0.0,
            fadeOutTime=3.0,
        )
        _call("builders.limb_builder", "build_limb", side=side, limb=limb)

    cmds.button(label="Build", command=_run)
    cmds.showWindow(win)


# ---------------------------------------------------------------------------
# Button launcher - each shelf button calls launch("<key>")
# ---------------------------------------------------------------------------


def launch(key):
    """Dispatch a shelf button key to its tool function."""
    _ensure_repo_on_path()

    # --- QC tools (read-only scene validation) -----------------------------
    if key == "select_ctl":
        _call("qc.select_controllers", "select_all")
    elif key == "naming":
        _call("qc.naming_validator", "check_controllers")
    elif key == "zero_tf":
        _call("qc.zero_transform_check", "check_zero_transforms")
    elif key == "unparented":
        _call("qc.unparented_controls", "check_hierarchy")
    elif key == "joint_orient":
        _call("qc.joint_orient_check", "check_joint_orient")
    elif key == "double_tf":
        _call("qc.double_transform_detector", "check_double_transforms")

    # --- Setup tools (one scene write each) ---------------------------------
    elif key == "make_ctl":
        _prompt_make_controller()
    elif key == "rename":
        # Scene-wide L_ -> R_ flip (tool defaults); see tooltip.
        _call("setup.rename_hierarchy", "rename_by_pattern")
    elif key == "rename_ui":
        # Batch rename window (ux package, Fase 4 UI over Fase 2 logic).
        _call("ux.rename_ui", "open_rename_window")
    elif key == "constraint":
        # Driver(s) first, driven last, in the selection.
        _call(
            "setup.constraint_assistant",
            "constraint_from_selection",
            constraint_type="parent",
        )
    elif key == "mirror":
        _call("setup.mirror_joint_tool", "mirror_from_selection", axis="X")

    # --- Builders (multi-step) ----------------------------------------------
    elif key == "build_limb":
        _build_limb_dialog()
    elif key == "build_spine":
        _call("builders.spine_builder", "build_spine", phase="setup")

    # --- Library (control shape library) ------------------------------------
    elif key == "control_library":
        # One-click import of saved control shapes (.mb per control).
        _call("library.gui", "open_library_window")

    else:
        import maya.cmds as cmds

        cmds.warning("pt_rigtools_shelf: unknown key '%s'" % key)


# ---------------------------------------------------------------------------
# Shelf construction
# ---------------------------------------------------------------------------


def _button_specs():
    """One entry per shelf button: label, tooltip, icon, launcher key.

    Icons are Maya built-ins (resolved via MAYA_BUTTON_PATH), verified
    against Maya 2027's icons folder.
    """
    return [
        # label, annotation (tooltip), image, launch key
        (
            "Sel Ctls",
            "Select all *_ctl controllers in the scene.",
            "select.xpm",
            "select_ctl",
        ),
        (
            "Naming",
            "QC: controllers missing the L_/R_/C_ prefix.",
            "channels.png",
            "naming",
        ),
        (
            "Zero TF",
            "QC: controllers with non-zero T/R at rest pose.",
            "ResetMode.png",
            "zero_tf",
        ),
        (
            "Unparent",
            "QC: controllers outside the RIG top group.",
            "genericGroupIcon.xpm",
            "unparented",
        ),
        (
            "Jnt Orient",
            "QC: rotation in .rotate instead of .jointOrient.",
            "pivotIcon.xpm",
            "joint_orient",
        ),
        (
            "Dbl TF",
            "QC: parent/child pairs that both carry transforms.",
            "out_floatMath.png",
            "double_tf",
        ),
        (
            "Make Ctl",
            "Create a controller (_off/_auto/_grp/_ctl hierarchy). Prompts for name+side.",
            "hollowBoxIcon.xpm",
            "make_ctl",
        ),
        (
            "Rename L>R",
            "Scene-wide rename L_ -> R_ (tool defaults).",
            "text.xpm",
            "rename",
        ),
        (
            "Rename UI",
            "Batch rename window: find/replace, prefix/suffix, numbering - always preview first.",
            "text.xpm",
            "rename_ui",
        ),
        (
            "Constrain",
            "Parent-constrain from selection: driver(s) first, driven last.",
            "constrainedMotion.xpm",
            "constraint",
        ),
        (
            "Mirror Jnt",
            "Mirror selected joints across X, flipping L_/R_.",
            "quickshadow.xpm",
            "mirror",
        ),
        (
            "Build Limb",
            "FK/IK triple-chain limb builder (two-pass). Dialog for side/limb.",
            "HIKik.png",
            "build_limb",
        ),
        (
            "Build Spine",
            "Spline IK spine from endpoints + editable curve.",
            "ikSplineManip.xpm",
            "build_spine",
        ),
        (
            "Ctrl Library",
            "Control shape library: click a button to import a saved control (.mb) into the scene. Ctrl+E exports the selection to the library.",
            "pythonFamily.png",
            "control_library",
        ),
    ]


def ensure_shelf(rebuild=False):
    """Create the PT_RigTools shelf if missing (or force rebuild).

    Only creates when missing, so manual edits made later in the Shelf
    Editor are respected across restarts. rebuild=True wipes the shelf
    BUTTONS and regenerates them - use after editing this file.

    GOTCHA (hit in practice): addNewShelfTab RESTORES the shelf from
    its saved prefs file (prefs/shelves/shelf_PT_RigTools.mel) when one
    exists, so a "fresh" tab comes pre-loaded with the OLD buttons.
    Recreating the tab on rebuild used to duplicate every button. The
    fix: keep the tab, wipe its children, add exactly one per spec.
    """
    import maya.cmds as cmds
    import maya.mel as mel

    if not os.path.isdir(REPO_PATH):
        # Dead buttons are worse than no shelf: refuse to build and say why.
        cmds.warning(
            "pt_rigtools_shelf: repo not found at %s - shelf not built. "
            "Clone maya-rigging-tools or update REPO_PATH." % REPO_PATH
        )
        return

    if cmds.shelfLayout(SHELF_NAME, exists=True):
        if not rebuild:
            return
    else:
        # addNewShelfTab creates the tab AND registers it in shelf prefs
        # (and restores saved content - the wipe below clears that).
        try:
            mel.eval('addNewShelfTab "%s"' % SHELF_NAME)
        except Exception:
            # Fallback for any future version dropping that MEL proc.
            cmds.shelfLayout(SHELF_NAME, parent=mel.eval("$g = $gShelfTopLevel"))

    # Wipe existing buttons (restored from prefs or an older build) so
    # the loop below adds exactly one of each - no duplicates possible.
    for child in cmds.layout(SHELF_NAME, query=True, childArray=True) or []:
        cmds.deleteUI(child)

    for label, ann, image, key in _button_specs():
        cmds.shelfButton(
            parent=SHELF_NAME,
            label=label,
            annotation=ann,
            image=image,
            sourceType="python",
            command='import pt_rigtools_shelf as pt; pt.launch("%s")' % key,
        )
