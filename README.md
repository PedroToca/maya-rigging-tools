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

## Shelf — PT_RigTools (one-click access)

`shelf/pt_rigtools_shelf.py` generates a **PT_RigTools** shelf tab with one
button per tool. The shelf is built from code — not saved as a prefs file —
so it rebuilds itself if prefs are reset or the repo gains tools, and the
buttons import straight from the repo clone (a `git pull` updates the tools
instantly, nothing is copied into Maya).

### Install (once per Maya version)

1. Copy `shelf/pt_rigtools_shelf.py` into `<Documents>/maya/<version>/scripts/`
   and check that `REPO_PATH` (top of the file) points at your clone.
2. Optional autostart — add this line to `userSetup.mel` in that same folder:

   ```mel
   evalDeferred "python(\"import pt_rigtools_shelf; pt_rigtools_shelf.ensure_shelf()\")";
   ```

### Rebuild (after editing buttons or REPO_PATH)

```python
import importlib, pt_rigtools_shelf
importlib.reload(pt_rigtools_shelf)
pt_rigtools_shelf.ensure_shelf(rebuild=True)
```

The `reload` is required — a plain import reuses the cached module. The
rebuild wipes the shelf buttons and regenerates exactly one per tool (Maya's
`addNewShelfTab` restores saved prefs content, so deleting and recreating the
tab duplicates every button).

### Buttons and what they need from you

A shelf button is a single click, so it fits three tiers: zero-argument
actions are plain buttons; tools that need a couple of parameters ask with a
small prompt or dialog; genuinely multi-step tools open a full window —
a bare button can't collect multi-step input.

| Button | Tool | Action | Input it needs |
|---|---|---|---|
| Sel Ctls | `qc/select_controllers` | Select all `*_ctl` in the scene | none |
| Naming | `qc/naming_validator` | QC: controllers missing `L_/R_/C_` prefix | none |
| Zero TF | `qc/zero_transform_check` | QC: non-zero translate/rotate at rest | none |
| Unparent | `qc/unparented_controls` | QC: controllers outside the rig top group | none |
| Jnt Orient | `qc/joint_orient_check` | QC: rotation in `.rotate` instead of `.jointOrient` | none |
| Dbl TF | `qc/double_transform_detector` | QC: parent/child pairs both carrying transforms | none |
| Make Ctl | `setup/controller_maker` | Create `_off/_auto/_grp/_ctl` control stack | prompt: name + side |
| Rename L>R | `setup/rename_hierarchy` | Scene-wide `L_` -> `R_` flip (tool defaults) | none |
| Rename UI | `ux/rename_ui` | Batch rename window — always preview first | own window |
| Constrain | `setup/constraint_assistant` | Parent-constrain from selection | selection: driver(s) first, driven last |
| Mirror Jnt | `setup/mirror_joint_tool` | Mirror selected joints across X, flipping `L_/R_` | selection |
| Build Limb | `builders/limb_builder` | FK/IK triple-chain limb (two-pass) | dialog: side + limb |
| Build Spine | `builders/spine_builder` | Spline IK spine from endpoints + editable curve | none |
| Ctrl Library | `library/gui` | Control shape library — click to import saved controls | own window |

## Requirements

- Autodesk Maya 2025+ (embedded Python 3.11)
- No external dependencies — `maya.cmds` only

## License

[MIT](LICENSE)
