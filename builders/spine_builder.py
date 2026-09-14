"""
spine_builder.py
================
Spline IK spine builder driven by an editable curve.

The spine is defined by TWO endpoint locators (hips + chest). An editable
curve (5 collinear CVs, degree 3) is created between them: it renders as a
straight line but can be sculpted freely. Joints are distributed along the
curve via pointOnCurve at a uniform parameter — equidistance is guaranteed
by design, not by the artist's hand.

The SAME curve then drives the spline IK solver, so what the artist shapes
is exactly what the rig uses.

Workflow (two-phase, like limb_builder):
    build_spine(phase="setup")   # endpoints + curve
    # -> position the locators, sculpt the curve's middle CVs if needed
    build_spine(phase="build")   # joints + spline IK + controls

Requirements:
    - setup.controller_maker.make_controller_at_position (returns (_off, _ctl))
    - Naming: C_ prefix (center), _loc / _crv / _jnt / _cl / _ctl suffixes

Examples:
    >>> build_spine("setup")   # then place & sculpt
    >>> build_spine("build")
"""

import maya.cmds as cmds
from setup.controller_maker import make_controller_at_position


def lerp(a, b, t):
    """
    Brief: Linear interpolation between two 3D points.

    Args:
        a (list): Start point [x, y, z].
        b (list): End point [x, y, z].
        t (float): Fraction (0 = a, 1 = b).

    Returns:
        list: The interpolated point [x, y, z].
    """
    return [a[k] + (b[k] - a[k]) * t for k in range(3)]


def create_spine_endpoints(height=20.0):
    """
    Brief: Create the two endpoint locators (hips at origin, chest above).

    Args:
        height (float): Default Y height for the chest locator.

    Returns:
        None. Creates C_hips_loc and C_chest_loc.
    """
    # Two-pass flow: keep existing locators (already positioned by the
    # artist). Re-creating would spawn suffixed duplicates and reset the
    # chest to default height.
    if cmds.objExists("C_hips_loc") and cmds.objExists("C_chest_loc"):
        return
    cmds.spaceLocator(name="C_hips_loc")
    chest = cmds.spaceLocator(name="C_chest_loc")[0]
    cmds.setAttr(chest + ".ty", height)


def create_editable_curve(cvs=5):
    """
    Brief: Create the spine curve between the endpoints — born straight,
    sculptable by design.

    CVs are placed collinearly (lerp) with degree 3: the curve renders as
    a straight line, but every middle CV can be dragged to shape curvature.
    A 2-CV curve could never bend — the editability lives in the middle CVs.

    Args:
        cvs (int): Total CV count. More CVs = finer shaping, more to maintain.

    Returns:
        str: The curve transform name (C_spine_crv).
    """
    hips = cmds.xform("C_hips_loc", query=True, worldSpace=True, translation=True)
    chest = cmds.xform("C_chest_loc", query=True, worldSpace=True, translation=True)
    points = [tuple(lerp(hips, chest, i / (cvs - 1))) for i in range(cvs)]
    return cmds.curve(name="C_spine_crv", p=points, d=3)


def create_spine_joints(count=4):
    """
    Brief: Distribute the spine joints along the curve at uniform parameter.

    Joints sit at u = i/(count-1) — endpoints INCLUDED, spacing guaranteed
    by parameter. They are placed ONCE: sculpt the curve BEFORE this runs.

    Args:
        count (int): Number of spine joints (hips and chest included).

    Returns:
        None. Creates C_spine01_jnt ... C_spine{count}_jnt, chained.
    """
    crv = "C_spine_crv"
    cmds.select(clear=True)  # joints chain under the selected one
    for i in range(count):
        u = i / (count - 1)  # 0 ... 1, endpoints included
        # turnOnPercentage=True: parameter normalized to 0-1.
        # Without it, parameter runs over the knot domain (0..spans)
        # and the chain would cover only a fraction of the curve.
        pos = cmds.pointOnCurve(crv, parameter=u, position=True, turnOnPercentage=True)
        cmds.joint(name=f"C_spine{i + 1:02d}_jnt", position=pos)


def create_spine_ik():
    """
    Brief: Create the spline IK handle over the spine curve.

    Uses curve="C_spine_crv" with createCurve=False so the solver adopts
    THE user-shaped curve. Without createCurve=False Maya builds its own
    curve and editing the original does nothing.

    Returns:
        str: The IK handle name.
    """
    joints = cmds.ls("C_spine*_jnt") or []
    handle, _effector = cmds.ikHandle(
        name="C_spineIKHandle",
        startJoint=joints[0],
        endEffector=joints[-1],
        solver="ikSplineSolver",
        curve="C_spine_crv",
        createCurve=False,
    )
    return handle


def create_spine_controls(handle):
    """
    Brief: Cluster the curve's end CVs and drive them with controls.

    Total CVs of a curve = degree + spans — used to reach the LAST CV
    without hardcoding its index. A twist attribute on the top control
    feeds the spline handle's twist.

    Args:
        handle (str): IK handle from create_spine_ik().

    Returns:
        None. Creates C_spineroot_ctl / C_spinetop_ctl (+_cl clusters).
    """
    crv = "C_spine_crv"
    cvs = cmds.getAttr(crv + ".degree") + cmds.getAttr(crv + ".spans")
    for tag, cv_index in [("root", 0), ("top", cvs - 1)]:
        # cluster returns [transform, handle] — the handle is [1]
        cl = cmds.cluster(f"{crv}.cv[{cv_index}]", name=f"C_spine{tag}_cl")[1]
        cv_pos = cmds.pointPosition(f"{crv}.cv[{cv_index}]")
        _off, ctl = make_controller_at_position(f"spine{tag}", "C_", cv_pos)
        cmds.parentConstraint(ctl, cl, maintainOffset=True)

    top_ctl = "C_spinetop_ctl"
    cmds.addAttr(
        top_ctl, longName="twist", attributeType="float", defaultValue=0, keyable=True
    )
    cmds.connectAttr(f"{top_ctl}.twist", f"{handle}.twist")


def build_spine(phase="setup"):
    """
    Brief: Orchestrator — two-phase build, the artist decides when to commit.

    Args:
        phase (str): "setup" creates endpoints + editable curve;
            "build" creates joints + spline IK + controls. Position and
            sculpt between phases.

    Returns:
        None.
    """
    if phase == "setup":
        create_spine_endpoints()
        create_editable_curve()
    elif phase == "build":
        # joints first — the IK handle needs them to exist
        create_spine_joints()
        handle = create_spine_ik()
        create_spine_controls(handle)
