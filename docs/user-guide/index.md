# User Guide

This guide walks you through using Flow3R to set up and run a recording session.

---

## Overview

Flow3R is organised around three concepts:

| Concept | What it is |
|---|---|
| **Source** | A single input device or file (webcam, microphone, video file, …) |
| **Recording group** | A named collection of sources that are recorded together |
| **Pipeline** | A processing step attached to a group (record video, analyse pose, …) |

A typical workflow:

1. Add and configure **sources**
2. Create a **recording group** and assign sources to it
3. Attach one or more **pipelines** to the group
4. Set **placeholder** values (animal ID, experiment name, …)
5. Press **Record**

---

## Adding sources

*Documentation coming soon — add screenshots here.*

---

## Recording groups

### Explicit groups

Explicit groups are created by the user in the **Groups** panel.  Each group has its own recording controls, file path settings, and pipeline list.

### Implicit groups

Any source that is not assigned to an explicit group appears in an automatically managed *implicit group*.  Implicit groups cannot be renamed or deleted — assign the source to an explicit group to take full control.

---

## Pipelines

A pipeline defines what happens to the data from a group's sources during a recording session.  Multiple pipelines can be attached to one group and they all run simultaneously.

Built-in pipeline types:

| Pipeline | Description |
|---|---|
| **Record Video** | Encodes video from a video source to a file |
| **Record Audio** | Records audio from an audio source to a file |
| **Record Video with Audio** | Records synchronised video+audio to a single container |

Additional pipelines (pose estimation, grimace scale, …) are provided by optional plugins.

---

## Placeholders

Placeholders are named template variables that you define once and reuse in file paths and metadata.  They appear as `{variable_name}` in path templates.

| Persistence | Meaning |
|---|---|
| `session` | Value is forgotten when the application restarts |
| `project` | Value is saved in the `.f3r` project file |
| `recording` | Value is reset automatically after each recording |

**Global placeholders** (e.g. `{experimenter}`) are shared across all groups.  **Group-scoped placeholders** (e.g. `{animal_id}`) belong to a single group.

---

## Saving and loading projects

Use **File → Save Project** to write the full configuration (sources, groups, pipelines, placeholder definitions) to a `.f3r` YAML file.  Open it again with **File → Open Project**.

> **Backwards compatibility:** `.f3r` files from older versions are automatically migrated when loaded. See [CHANGELOG](../../CHANGELOG.md) for schema changes between versions.

