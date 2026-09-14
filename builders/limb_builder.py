"""
limb_builder.py
===============
Generic limb rig builder with a triple-chain (skin / FK / IK) architecture.

Builds a complete FK/IK limb (leg, arm, or any chain defined in LIMB_JOINTS)
from locator positions. The production-standard architecture keeps three
separate joint chains:

    skin chain  -> the deformation skeleton that gets skinned to the mesh
    fk chain    -> driven by the FK controls (rotation-based animation)
    ik chain    -> driven by the IK handle (position-based animation)

Both control chains parentConstrain the skin chain. A custom fkik attribute
on the IK control blends between the two constraint weights via a reverse
node, so the animator can switch modes without breaking either setup.

Workflow:
    1. Run build_limb() -> creates locators for the limb.
    2. Position the locators in the viewport where joints should be.
    3. Comment out the create_limb_locators() call (or delete the locators'
       placement) and run build_limb() again to build the rig.

Requirements:
    - Locators must exist at build time: <side><jointName>_loc
    - Naming convention: L_legUp_skin_jnt, L_legUp_fk_ctl, L_legIK_ctl...
    - The limb must have at least 3 joints (start, middle, end) for IK.

Examples:
    >>> build_limb(side="L_", limb="leg")   # leg: legUp / legLow / ankle
    >>> build_limb(side="L_", limb="arm")   # arm: armUp / armLow / wrist
"""

import maya.cmds as cmds

# Data-driven definition of limbs: each limb maps to its ordered joint names.
# Adding a new limb only requires a new entry here — every function below
# derives its names from this mapping.
LIMB_JOINTS = {
    "leg": ["legUp", "legLow", "ankle"],
    "arm": ["armUp", "armLow", "wrist"],
}


def create_limb_locators(side="L_", limb="leg"):
    """
    Brief: Create one locator per joint of the limb, at the origin.

    The user positions these in the viewport; every joint chain is then built
    from the locators' world positions.

    Args:
        side (str): Side prefix. Defaults to "L_".
        limb (str): Limb key in LIMB_JOINTS. Defaults to "leg".

    Returns:
        None.
    """
    joint_names = LIMB_JOINTS[limb]
    for name in joint_names:
        cmds.spaceLocator(name=f"{side}{name}_loc")


def create_joint_chain(side="L_", limb="leg", chain_type="skin"):
    """
    Brief: Create one joint chain of the given type, reading locator positions.

    Each joint is placed at its locator's position. Joints stay selected after
    creation, so each subsequent cmds.joint() automatically chains under the
    previous one and Maya computes the parent's jointOrient to aim at its child.

    Args:
        side (str): Side prefix. Defaults to "L_".
        limb (str): Limb key in LIMB_JOINTS. Defaults to "leg".
        chain_type (str): Chain suffix. Defaults to "skin".
            Valid: "skin", "fk", "ik".

    Returns:
        None.
    """
    joint_names = LIMB_JOINTS[limb]
    # Without this, the new chain would parent under the last joint of a
    # previously created chain (selection persists between joint() calls)
    cmds.select(clear=True)
    for name in joint_names:
        jointName = f"{side}{name}_{chain_type}_jnt"
        # Locators have no parent, so .translate equals world position
        poslist = cmds.getAttr(f"{side}{name}_loc" + ".translate")
        pos = poslist[0]
        cmds.joint(name=jointName, position=pos)


def create_all_chains(side="L_", limb="leg"):
    """
    Brief: Create the three chains (skin, fk, ik) for a limb.

    Orchestrator for create_joint_chain() — one call builds the whole
    triple-chain structure.

    Args:
        side (str): Side prefix. Defaults to "L_".
        limb (str): Limb key in LIMB_JOINTS. Defaults to "leg".

    Returns:
        None.
    """
    for chain_type in ["skin", "fk", "ik"]:
        create_joint_chain(side, limb, chain_type)


def make_controller(name, side="L_"):
    """
    Brief: Create a controller with its offset hierarchy at the origin.

    Hierarchy built: _off -> _auto -> _grp -> _ctl. The _off group absorbs
    world position and parenting so the _ctl stays zeroed at rest.

    Args:
        name (str): Full name prefix AFTER the side (e.g. "legUp_fk",
            "legIK", "legPV"). The chain type is baked in by the caller.
        side (str): Side prefix. Defaults to "L_".

    Returns:
        tuple: (off_name, ctl_name) so callers can chain and parent.
    """
    controllername = (side + name)
    # circle returns [transform, shape] — [0] grabs the transform
    ctl = cmds.circle(name=controllername + "_ctl")[0]
    grp = cmds.group(name=controllername + "_grp")
    auto = cmds.group(name=controllername + "_auto")
    off = cmds.group(name=controllername + "_off")

    cmds.parent(ctl, grp)
    cmds.parent(grp, auto)
    cmds.parent(auto, off)

    return off, ctl


def make_controller_at_position(name, side="L_", position=(0, 0, 0)):
    """
    Brief: Create a controller and place it at a world-space position.

    The position is applied to the _off group (not the _ctl) to keep the
    control's own transforms zeroed.

    Args:
        name (str): Full name prefix AFTER the side.
        side (str): Side prefix. Defaults to "L_".
        position (tuple): World-space (x, y, z) position.

    Returns:
        tuple: (off_name, ctl_name).
    """
    off, ctl = make_controller(name, side)
    cmds.xform(off, worldSpace=True, translation=position)
    return off, ctl


def create_fk_controls(side="L_", limb="leg"):
    """
    Brief: Create one FK control per FK joint and chain them together.

    Each control parents its matching FK joint. Each subsequent control's _off
    is parented under the previous control's _ctl, producing the classic FK
    chain: rotating a parent control carries everything below it.

    Args:
        side (str): Side prefix. Defaults to "L_".
        limb (str): Limb key in LIMB_JOINTS. Defaults to "leg".

    Returns:
        None.
    """
    joint_names = LIMB_JOINTS[limb]
    # Remembers the previous iteration's control — the chaining reference
    prev_ctl = None
    for name in joint_names:
        # World-space position (xform ws=True), because a chained joint's
        # .translate is LOCAL to its parent, not world
        pos = cmds.xform(f"{side}{name}_fk_jnt", query=True, worldSpace=True, translation=True)
        off, ctl = make_controller_at_position(f"{name}_fk", side, pos)
        joint = f"{side}{name}_fk_jnt"
        cmds.parent(joint, ctl)
        if prev_ctl:
            # Chain through the _off so the _ctl stays zeroed
            cmds.parent(off, prev_ctl)
        prev_ctl = ctl


def create_ik(side, limb):
    """
    Brief: Create the IK system for the limb's IK chain.

    Builds three pieces: an IK handle spanning first -> last IK joint, an end
    control that drives the handle, and a pole vector control that steers the
    bend direction of the middle joint.

    Args:
        side (str): Side prefix (e.g. "L_").
        limb (str): Limb key in LIMB_JOINTS (e.g. "leg").

    Returns:
        None. Creates: {side}{limb}IKHandle, {side}{limb}IK_ctl, {side}{limb}PV_ctl.

    Notes:
        - ikRPsolver (rotate plane) is required for poleVectorConstraint to work.
        - Indexing assumes a 3-joint chain: [0] start, [1] middle, [-1] end.
    """
    joint_names = LIMB_JOINTS[limb]
    first_joint = f"{side}{joint_names[0]}_ik_jnt"
    last_joint = f"{side}{joint_names[-1]}_ik_jnt"
    middle_joint = f"{side}{joint_names[1]}_ik_jnt"

    # ikHandle returns [handle, effector] — the handle is what the control drives
    ik_handle, ik_effector = cmds.ikHandle(
        name=f"{side}{limb}IKHandle",
        startJoint=first_joint,
        endEffector=last_joint,
        solver="ikRPsolver"
    )

    # End control at the last joint — driver first, driven second
    pos = cmds.xform(last_joint, query=True, worldSpace=True, translation=True)
    off, ik_ctl = make_controller_at_position(f"{limb}IK", side, pos)

    cmds.pointConstraint(ik_ctl, ik_handle, maintainOffset=True)

    # Pole vector at the middle joint steers the chain's bend direction
    pv_pos = cmds.xform(middle_joint, query=True, worldSpace=True, translation=True)
    off, pv_ctl = make_controller_at_position(f"{limb}PV", side, pv_pos)
    cmds.poleVectorConstraint(pv_ctl, ik_handle)


def connect_chains(side, limb):
    """
    Brief: parentConstrain every FK and IK joint onto its skin counterpart.

    Each skin joint receives TWO parentConstraints (one from FK, one from IK).
    Their weights are both 1.0 at creation, so the skin averages both chains —
    the switch in create_switch() is what makes only one active at a time.

    Args:
        side (str): Side prefix (e.g. "L_").
        limb (str): Limb key in LIMB_JOINTS (e.g. "leg").

    Returns:
        list[tuple]: (fk_constraint_node, ik_constraint_node) per joint.
        Needed by create_switch() to wire the blend weights.
    """
    joint_names = LIMB_JOINTS[limb]
    all_constraints = []

    for name in joint_names:
        fk_joint = f"{side}{name}_fk_jnt"
        ik_joint = f"{side}{name}_ik_jnt"
        skin_joint = f"{side}{name}_skin_jnt"

        # parentConstraint returns a list — [0] extracts the node name
        fk_con = cmds.parentConstraint(fk_joint, skin_joint, maintainOffset=True)[0]
        ik_con = cmds.parentConstraint(ik_joint, skin_joint, maintainOffset=True)[0]
        all_constraints.append((fk_con, ik_con))
    return all_constraints


def create_switch(side, limb, constraints):
    """
    Brief: Build the FK/IK switch that blends the two constraint sets.

    Adds a custom fkik float attribute (0 = FK, 1 = IK) on the IK control and
    wires it through a single reverse node:

        fkik -> reverse.inputX -> reverse.outputX -> FK constraint weight
        fkik ------------------------------------> IK constraint weight

    fkik = 1 -> reverse outputs 0 -> FK off, IK on.
    fkik = 0 -> reverse outputs 1 -> FK on, IK off.

    Args:
        side (str): Side prefix (e.g. "L_").
        limb (str): Limb key in LIMB_JOINTS (e.g. "leg").
        constraints (list[tuple]): Constraint pairs from connect_chains().

    Returns:
        None.
    """
    ik_ctl = f"{side}{limb}IK_ctl"
    cmds.addAttr(ik_ctl, longName="fkik", attributeType="float", minValue=0, maxValue=1, defaultValue=1)
    # One reverse node serves the whole limb
    reverse = cmds.createNode("reverse")
    cmds.connectAttr(f"{ik_ctl}.fkik", f"{reverse}.inputX")
    for fk_con, ik_con in constraints:
        # Each constraint has a single target, so its weight is always targetW0
        cmds.connectAttr(f"{reverse}.outputX", f"{fk_con}.targetW0")
        cmds.connectAttr(f"{ik_ctl}.fkik", f"{ik_con}.targetW0")


def build_limb(side="L_", limb="leg"):
    """
    Brief: Full limb build — orchestrates every step of the pipeline.

    Order matters: locators -> chains -> controls -> constraints -> switch.

    Args:
        side (str): Side prefix. Defaults to "L_".
        limb (str): Limb key in LIMB_JOINTS. Defaults to "leg".

    Returns:
        None.
    """
    create_limb_locators(side, limb)
    create_all_chains(side, limb)
    create_fk_controls(side, limb)
    create_ik(side, limb)
    constraints = connect_chains(side, limb)
    create_switch(side, limb, constraints)
