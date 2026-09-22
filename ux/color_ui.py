"""color_ui - One-click color override for controllers.

WHAT: A cmds window showing Maya's 32 drawing-override index colors as
REAL color swatches (painted with colorIndex queries, so the window shows
the same RGB the viewport will draw). Click a swatch -> every selected
controller gets that overrideColor in ONE undo step.

WHY SHAPE-LEVEL: the override lives on each SHAPE node (the manual path:
shape -> Object Display -> Drawing Overrides). A controller transform can
hold several curve shapes, so the tool colors ALL of them - painting only
the first shape leaves a half-colored control.

WHY colorIndex: it queries the RGB of each palette entry, which is what
lets the UI show colors instead of numbers - the number alone is useless
when you are hunting "the teal one".

Usage (Script Editor):
    from ux.color_ui import open_color_window
    open_color_window()

Course references: 04.1 Windows y layouts (5-step window pattern),
04.2 Widgets (default-arg lambdas against late binding), 04.3 scriptJob
reactive UI (SelectionChanged parented to the window, dies with it).
"""

import maya.cmds as cmds

WINDOW_NAME = "ptColorWin"

# The classic drawing-override palette: 32 entries, index 0-31.
PALETTE_SIZE = 32
COLUMNS = 8

# Shape types a controller color applies to. Curves are the norm; mesh
# shapes are included so surface controllers work too.
CONTROLLER_SHAPE_TYPES = ("nurbsCurve", "mesh")


# ---------------------------------------------------------------------------
# Logic - plain functions, testable without opening the window
# ---------------------------------------------------------------------------


def collect_shapes(nodes):
    """Shape paths to color for the given nodes.

    Transforms contribute ALL their controller shapes; a shape selected
    directly in the outliner (shape mode) is kept as-is. Anything else
    (joints, deformers...) yields nothing - this tool colors geometry.
    """
    shapes = []
    for node in nodes:
        ntype = cmds.nodeType(node)
        if ntype == "transform":
            relatives = cmds.listRelatives(node, shapes=True, fullPath=True) or []
            shapes += [
                s for s in relatives if cmds.nodeType(s) in CONTROLLER_SHAPE_TYPES
            ]
        elif ntype in CONTROLLER_SHAPE_TYPES:
            shapes.append(node)
    return shapes


def set_control_color(index, nodes=None):
    """Apply overrideColor=index to all controller shapes of the selection.

    Returns the number of shapes colored. One undo chunk for the whole
    batch: coloring 20 controls must revert with a single Ctrl+Z, not 20.

    Locked/referenced shapes can reject setAttr - they are collected and
    reported at the end instead of stopping the batch halfway.
    """
    if not 0 <= index < PALETTE_SIZE:
        cmds.warning("color_ui: index %r out of range 0-%d" % (index, PALETTE_SIZE - 1))
        return 0

    if nodes is None:
        nodes = cmds.ls(selection=True, long=True) or []
    if not nodes:
        cmds.warning("color_ui: nothing selected - select controllers first")
        return 0

    shapes = collect_shapes(nodes)
    if not shapes:
        cmds.warning(
            "color_ui: selection has no curve/mesh shapes "
            "(controllers are curve transforms)"
        )
        return 0

    failed = []
    cmds.undoInfo(openChunk=True, chunkName="colorUI")
    try:
        for shape in shapes:
            try:
                cmds.setAttr(shape + ".overrideEnabled", 1)
                cmds.setAttr(shape + ".overrideColor", index)
            except Exception as err:
                # Locked or referenced attribute - keep coloring the rest.
                failed.append((shape, err))
    finally:
        cmds.undoInfo(closeChunk=True)

    if failed:
        cmds.warning(
            "color_ui: %d shape(s) rejected the override (locked/referenced?) "
            "- first: %s" % (len(failed), failed[0][0].split("|")[-1])
        )
    return len(shapes) - len(failed)


def current_color_index():
    """Override color index of the FIRST selected shape, None if none.

    Read-only query used by the window footer so you know where the
    selection stands before clicking.
    """
    shapes = collect_shapes(cmds.ls(selection=True, long=True) or [])
    if not shapes:
        return None
    if not cmds.getAttr(shapes[0] + ".overrideEnabled"):
        return None
    return cmds.getAttr(shapes[0] + ".overrideColor")


# ---------------------------------------------------------------------------
# UI - 5-step window pattern (exists -> delete -> create -> fill -> show)
# ---------------------------------------------------------------------------


def open_color_window():
    """Open the controller color window (idempotent - safe to call twice)."""
    if cmds.window(WINDOW_NAME, exists=True):
        cmds.deleteUI(WINDOW_NAME)

    # Explicit size: without widthHeight a non-resizable window does not
    # reliably shrink-wrap to its content (opened ~4x the grid size).
    # Grid math: 8 cells * 32px + 7 gaps * 4px = 284px wide core.
    win = cmds.window(
        WINDOW_NAME, title="Control Color", sizeable=False, widthHeight=(290, 245)
    )
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

    cmds.text(label="Control Color", font="boldLabelFont")
    cmds.text(label="Click a swatch to color the selection.", align="left")
    cmds.separator(height=6, style="in")

    # The palette, painted with its own RGB - colorIndex(i, query=True)
    # returns the [r, g, b] of index i, the exact colors Drawing Overrides
    # draws in the viewport.
    # NOTE: gridLayout has NO columnSpacing/rowSpacing flags - the single
    # generalSpacing flag covers both (verified against the command docs).
    cmds.gridLayout(
        numberOfColumns=COLUMNS,
        cellWidthHeight=(32, 32),
        generalSpacing=4,
    )

    def do_color(index):
        """Button handler: apply + report in the footer."""
        count = set_control_color(index)
        if count:
            _set_status("Colored %d shape(s) with index %d." % (count, index))

    for i in range(PALETTE_SIZE):
        rgb = cmds.colorIndex(i, query=True)
        # Default arg i=i beats late binding: without it every lambda
        # would read the loop's LAST index (lesson 04.2).
        cmds.button(
            label="",
            backgroundColor=(rgb[0], rgb[1], rgb[2]),
            annotation="Apply index %d" % i,
            command=lambda _args, i=i: do_color(i),
        )
    cmds.setParent("..")

    status_text = cmds.text(label="Nothing selected.", align="left")

    def refresh_status():
        """Footer: override color the first selected shape already has."""
        index = current_color_index()
        if index is None:
            label = "Nothing selected / no override."
        else:
            label = "Current color of selection: index %d" % index
        cmds.text(status_text, edit=True, label=label)

    def _set_status(label):
        cmds.text(status_text, edit=True, label=label)

    # Live footer on selection change. parent= kills the job with the
    # window, so no manual cleanup (lesson 04.3 reactive UI pattern).
    cmds.scriptJob(parent=win, event=("SelectionChanged", refresh_status))

    refresh_status()
    cmds.showWindow(win)
    # GEOMETRY GOTCHA (probed in Maya 2027): recreating a window with a
    # name Maya already saw RESTORES the old geometry and silently
    # ignores widthHeight - retain=False does NOT help. Forcing the size
    # AFTER showWindow is the only call that wins.
    cmds.window(win, edit=True, widthHeight=(290, 245))
