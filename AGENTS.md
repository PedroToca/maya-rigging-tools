# Repository Guidelines

## Project Overview

Maya rigging tools: QC validators, atomic setup tools, and rig builders for Autodesk Maya, structured as a learning path (read-only → single-write → multi-step). Pure `maya.cmds` on Maya's embedded Python 3.11 — no external dependencies, no packaging, no build system.

## Architecture & Data Flow

Four packages, no `__init__.py` files. `qc/`, `setup/`, `builders/` are isolated from each other (no cross-imports). `library/` is a layered stack where the modules DO import each other bottom-up (`paths` ← `files` ← `main` ← `gui`) but nothing imports out of it. Interaction level escalates by directory:

- **`qc/`** — read-only validators. Each `check_*` scans the scene (`cmds.ls`) and prints a report; never modifies anything.
- **`setup/`** — atomic writers. Each function does exactly one scene modification (create controller hierarchy, rename, constrain, mirror).
- **`builders/`** — multi-step rig construction. `limb_builder.py` is data-driven via the `LIMB_JOINTS` dict (`{'leg': [...], 'arm': [...]}`) and builds a triple-chain (skin/FK/IK) limb with a reverse-node FK/IK switch. `spine_builder.py` and `face_rig_assistant.py` are planned, not yet written.
- **`library/`** — control-shape library (M2-L09.12–17 course design, cmds UI instead of PySide2 since Maya 2025+ dropped PySide2). One `.mb` per control inside `library/_control_lib/`; `library/` modules raise on bad input (they run under `gui.py`, which catches and warns) — exception to the no-raise convention, by design. `.mb` files under `_control_lib/` are versioned on purpose.

**Data flow in builders**: locator positions → joint chains → controls → constraints → FK/IK switch. `build_limb()` is the orchestrator.

**Known duplication**: offset-hierarchy controller creation (`make_controller` / `make_controller_at_position`) exists in both `setup/controller_maker.py` and `builders/limb_builder.py`. The builder's copy evolved further (returns `(off, ctl)` nodes); the setup copy returns `None`. This is accepted learning-path duplication, not a shared module.

## Key Directories

| Directory | Purpose |
|---|---|
| `qc/` | Phase 1 — read-only scene validation (6 tools, complete) |
| `setup/` | Phase 2 — single-action scene modification (4 tools, complete) |
| `builders/` | Phase 3 — multi-step rig builders (1 of 3 done) |
| `library/` | Phase 4 — control-shape library: export/import `.mb` per control + cmds UI |

## Development Commands

No build or test tooling exists. Lint/format runs outside Maya via ruff (see Runtime/Tooling). Everything else runs inside Maya 2025+ (Python tab of the Script Editor):

```python
# QC check
from qc.zero_transform_check import check_zero_transforms

check_zero_transforms()

# Setup tool
from setup.controller_maker import make_controller

make_controller("arm", side="L_")

# Build a limb (two-pass: run once → position locators in viewport → delete and re-run)
from builders.limb_builder import build_limb

build_limb(side="L_", limb="leg")
```

Repo must be on `MAYA_SCRIPT_PATH` (or Maya's scripts dir) for imports to resolve. Alternatively, paste a file's contents into the Script Editor.

**Import gotcha**: the selection tool is `qc/Select_controllers.py` — capital S (README shows it lowercase). On case-sensitive filesystems, `from qc.select_controllers import ...` fails; use `qc.Select_controllers`.

## Code Conventions & Common Patterns

- **Module-level functions only** — no classes anywhere. One module per tool.
- **Naming convention (enforced by tools, follow it everywhere)**: side prefixes `L_ / R_ / C_`; suffixes `_ctl` (controllers), `_jnt` (joints), `_loc` (locators). Controller hierarchy is always `name_off → name_auto → name_grp → name_ctl`.
- **Two entry styles per tool**: by-name (e.g. `create_constraint(driver=..., driven=...)`) and from-selection (e.g. `constraint_from_selection()`), usually driver-first selection order.
- **Error handling**: `cmds.warning(...)` + early return for bad input (missing node, empty selection). No exceptions raised, no dialogs. Tolerances are `0.001` — a keyword arg in some `qc/` tools (`double_transform_detector`, `joint_orient_check`), hardcoded in others (`zero_transform_check`).
- **Side flipping**: mirror/rename tools take `search_replace=('L_','R_')` tuples; joint mirroring uses `cmds.mirrorJoint(mirrorBehavior=True)` with axis→plane mapping.
- **Renaming hierarchies**: reverse the `allDescendents` list (children-first) so long names stay valid during the pass (`setup/rename_hierarchy.py`).
- **Docstrings**: brief module-level purpose + per-function; plain prose, no format standard.
- **Validation rule by directory**: `qc/` must never modify the scene; `setup/` functions each perform exactly one write. New tools should respect this contract.

## Important Files

- `builders/limb_builder.py` — largest/most advanced module; `LIMB_JOINTS` dict at top defines limb skeletons; `build_limb()` is the entry point.
- `setup/controller_maker.py` — canonical offset-hierarchy pattern (`_off/_auto/_grp/_ctl` with `makeIdentity` freeze).
- `qc/naming_validator.py` — reference for the naming-convention checks (`startswith(('L_','R_','C_'))`).
- `README.md` — roadmap with phase status, per-tool tables, usage examples.
- `.gitignore` — Python caches, IDE dirs, `.venv` only.

## Runtime/Tooling Preferences

- **Runtime**: Maya 2025+ embedded Python 3.11. Code is not runnable outside Maya (imports `maya.cmds`).
- **Dependencies**: none beyond `maya.cmds`. Do not add external packages.
- **Package manager**: none. No `requirements.txt`, `pyproject.toml`, or lock files — keep it that way.
- **Formatting/lint**: ruff, run via `uvx ruff format .` / `uvx ruff check .` (no install — uvx caches the binary). `ruff.toml` pins `target-version = "py311"` so 3.12+ syntax that Maya would reject gets flagged; ignores `PLR0402` (Maya idiom `import maya.cmds as cmds`) and `EXE002`. A pre-commit hook lives at `.githooks/pre-commit` (versioned — formats+checks staged `.py` files and re-stages fixes). Prerequisite: `uv` must be on PATH or every commit fails with exit 127. Git never ships hooks enabled for security reasons, so after cloning run once: `git config core.hooksPath .githooks`.
- **License**: MIT (PedroToca, 2026).

## Testing & QA

No test suite, no test framework, no CI. Verification is manual: run tools in Maya's Script Editor against a test scene.

For new tools, minimum bar: exercise the function in Maya, confirm expected scene state / printed report. If adding automated tests later, `maya.standalone` (Maya's headless mode) is the viable path — the code has no mocks or injection seams, so testing requires Maya's runtime.
