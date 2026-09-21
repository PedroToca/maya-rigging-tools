# Maya Rigging Tools

A collection of QC, setup, and rig-building tools for Autodesk Maya, developed
as a structured learning path from read-only scene validation to production-grade
rig builders.

All tools use `maya.cmds` (Python 3.11) and follow a strict naming convention:
`L_ / R_ / C_` side prefixes, `_ctl` for controllers, `_jnt` for joints,
`_loc` for locators.

## Roadmap

### Phase 1 — QC tools (read-only) ✅

Scene validation tools that never modify the scene. Safe to run on any rig.

| Tool | What it does |
|---|---|
| `qc/select_controllers.py` | Select all controllers, filter by side, keep only visible ones |
| `qc/naming_validator.py` | Detect controllers missing the `L_/R_/C_` prefix |
| `qc/zero_transform_check.py` | Detect controllers with non-zero translate/rotate at rest |
| `qc/unparented_controls.py` | Detect controllers living outside the rig's top-level group |
| `qc/joint_orient_check.py` | Detect joints with rotation in `.rotate` instead of `.jointOrient` |
| `qc/double_transform_detector.py` | Detect parent/child pairs that both carry transforms |

### Phase 2 — Setup tools (single write action) ✅

Atomic scene-modifying tools — each does exactly one thing.

| Tool | What it does |
|---|---|
| `setup/controller_maker.py` | Create controllers with the standard `_off/_auto/_grp/_ctl` offset hierarchy |
| `setup/rename_hierarchy.py` | Batch find/replace renaming, scene-wide or scoped to a hierarchy |
| `setup/constraint_assistant.py` | Create any constraint type from names or selection |
| `setup/mirror_joint_tool.py` | Mirror joints with proper orientation and side-prefix flipping |

### Phase 3 — Rig builders (multi-step systems) 🟡

| Tool | What it does |
|---|---|
| `builders/limb_builder.py` | Generic FK/IK limb builder with triple-chain (skin/FK/IK) architecture and FK/IK switch |
| `builders/spine_builder.py` | Spline IK spine from 2 endpoints + editable curve — joints distributed via `pointOnCurve` (equidistant by design) |
| `builders/face_rig_assistant.py` | *Planned* — driven keys / blend shapes in batch |

### Phase 4 — Control library 🟢

Reusable controller-shape library. Each control is stored as ONE `.mb`
inside `library/_control_lib/` (the full `_off` offset stack), and the UI
gives one click-to-import button per file. Exports only world-level nodes
(Export Selection carries the whole parent hierarchy otherwise). Imports
use a per-file namespace, merged into root when names are free, so
clashes never fail. Importing is NOT undoable (Maya limitation).

| Module | What it does |
|---|---|
| `library/paths.py` | Resolve package dir (`__file__`), create the controls folder |
| `library/files.py` | List files, check name collisions, export selection to .mb |
| `library/main.py` | `exportControl` / `getControllers` / `importControl` |
| `library/gui.py` | Control Library window: import buttons, open-folder, reload, export |

## Usage

Run inside Maya's Script Editor (Python tab):

```python
# Example: run a QC check
from qc.zero_transform_check import check_zero_transforms

check_zero_transforms()

# Example: build a leg
from builders.limb_builder import build_limb

build_limb(side="L_", limb="leg")

# Example: open the control library window
from library.gui import open_library_window

open_library_window()
```

Or paste a tool's contents directly into the Script Editor and call its functions.

For `limb_builder`, the workflow is two-pass:
1. `build_limb()` once to create locators, then position them in the viewport.
2. Delete the locators-only pass and run `build_limb()` again to build the rig
   at those positions.

## Requirements

- Autodesk Maya 2025+ (embedded Python 3.11)
- No external dependencies — `maya.cmds` only

## License

[MIT](LICENSE)
