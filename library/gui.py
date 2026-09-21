"""
gui.py
=====
Control Library window - click-to-import buttons for every shape in
the library.

WHAT: a cmds window (same 5-step pattern as ux/rename_ui.py: exists ->
delete -> create -> fill -> show) with one button per .mb inside
library/_control_lib. File menu opens the folder in the OS explorer
and reloads the buttons; Utilities exports the current selection to
the library and refreshes. Course references: M2-L09.16 (window +
menus) and M2-L09.17 (reload + export-from-GUI), rebuilt on cmds
widgets instead of PySide2 (removed in Maya 2025+).

The window holds NO logic of its own - every action delegates to
library/main.py, so the whole tool also runs headless from the Script
Editor:

    from library.main import exportControl, importControl

Usage:
    from library.gui import open_library_window
    open_library_window()
"""

import os

import maya.cmds as cmds

from library import main, paths

WINDOW_NAME = "ptControlLibraryWin"
SCROLL_NAME = "ptControlLibraryScroll"
BUTTON_COL = "ptControlLibraryButtonCol"


def open_library_window():
    """Open the Control Library window (idempotent - safe to call
    twice; the old instance is deleted first)."""
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)

    # menuBar=True gives the window its own menu bar - the cmds
    # equivalent of QMainWindow.menuBar() in the course version.
    win = cmds.window(WINDOW_NAME, title="Control Library", sizeable=True, menuBar=True)
    _add_menus()

    cmds.columnLayout(adjustableColumn=True, rowSpacing=6)
    cmds.text(label="Control Library", font="boldLabelFont")
    cmds.text(
        label="One button per .mb in library/_control_lib - click to import.",
        align="left",
    )
    cmds.separator(height=8, style="in")

    # Scroll so 40 buttons never fight the screen height (the
    # QScrollArea of the course, on cmds).
    cmds.scrollLayout(SCROLL_NAME, horizontalScrollBarThickness=0, childResizable=True)
    load_buttons()

    cmds.showWindow(win)


def _add_menus():
    """File + Utilities menus.

    NOTE on shortcuts: cmds.menuItem has NO keyboard-accelerator flags
    in modern Maya - keyShortcut/ctrlModifier belong to cmds.hotkey
    (verified against maya-stubs). Registering global hotkeys would
    write into the user's Hotkey Editor, which is too invasive for
    this tool, so the Ctrl+O/R/E of the course's PySide2 version are
    dropped on purpose. Menu clicks remain.
    """
    cmds.menu(label="File")
    cmds.menuItem(label="Open Library Folder", command=_open_dir)
    cmds.menuItem(label="Reload Controls", command=_reload)
    cmds.menu(label="Utilities")
    cmds.menuItem(label="Export Selected Controls", command=_export_and_reload)


def load_buttons():
    """(Re)build the import buttons inside the scroll area.

    Called on window open AND on reload: the button column is deleted
    and recreated from scratch, so the UI always mirrors the folder -
    including files the user deleted by hand.
    """
    if cmds.columnLayout(BUTTON_COL, exists=True):
        cmds.deleteUI(BUTTON_COL)

    # Parent the new column INSIDE the scroll, wherever the current
    # layout sits when this is called.
    cmds.setParent(SCROLL_NAME)
    cmds.columnLayout(BUTTON_COL, adjustableColumn=True, rowSpacing=4)

    controls = main.getControllers()
    if not controls:
        cmds.text(
            label="(library is empty) Export world-level controls "
            "via the Utilities menu.",
            align="left",
        )
        return

    for control in controls:
        cmds.button(
            label="import " + control, height=30, command=_make_import_command(control)
        )


def _make_import_command(control):
    """Factory for per-button callbacks.

    A closure per button is the cmds stand-in for functools.partial:
    it freezes WHICH file the button imports. Defining the callback
    inline in the loop would late-bind and every button would import
    the last file - the classic closure trap.
    """

    def _import(_):
        try:
            main.importControl(controllers=[control])
        except Exception as e:
            # Keep the window alive: one broken .mb must not take
            # the whole UI down with it.
            cmds.warning(f"Control Library: {e}")

    return _import


def _open_dir(_):
    """File > Open Library Folder: create the folder if this is the
    very first run, then hand it to the OS explorer."""
    try:
        libDir = paths.createDir(
            path=paths.getCurrentDir(__file__),
            directory=main.CONTROL_DIR_NAME,
            silent=True,
        )
    except (ValueError, OSError) as e:
        cmds.warning(f"Control Library: {e}")
        return
    # cmds.launch is Maya's own - NOT this package's launch function.
    cmds.launch(dir=libDir)


def _reload(_):
    """File > Reload Controls: rebuild the button column."""
    load_buttons()
    print(f"Control Library: {len(main.getControllers())} control(s) loaded")


def _export_and_reload(_):
    """Utilities > Export Selected Controls (Ctrl+E).

    Export + refresh in one action, so a newly exported control gets
    its button immediately - no manual reload step in between.
    """
    valid, invalid = main.filter_export_selection()
    if not valid and not invalid:
        cmds.warning("Control Library: select at least one object.")
        return

    if invalid:
        cmds.warning(
            f"Control Library: skipping (under hierarchy): {', '.join(invalid)}"
        )
    if not valid:
        cmds.warning("Control Library: nothing valid to export.")
        return

    # Collisions get an explicit decision instead of a silent skip.
    libDir = main.control_dir()
    collisions = [v for v in valid if os.path.exists(os.path.join(libDir, v + ".mb"))]
    override = False
    if collisions:
        # ("\n" precomputed: py311 f-strings take no backslashes in
        # the expression part)
        existing = "\n".join(collisions)
        answer = cmds.confirmDialog(
            title="Control Library",
            message=(
                f"{len(collisions)} file(s) already exist:\n"
                f"{existing}\n\nOverwrite them?"
            ),
            button=["Overwrite", "Skip Existing"],
            defaultButton="Skip Existing",
            cancelButton="Skip Existing",
            dismissString="Skip Existing",
        )
        override = answer == "Overwrite"

    try:
        main.exportControl(stopIfInvalid=False, override=override)
    except Exception as e:
        cmds.warning(f"Control Library: {e}")
        return
    load_buttons()
