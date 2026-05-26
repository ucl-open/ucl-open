# Introduction

ucl-open is a platform for building standardised, reproducible experiment rigs in neuroscience. It separates the concerns of hardware configuration, task logic, and data acquisition into three collaborating parts: a Python schema library, a set of Bonsai operators, and a Copier project template.

## The three parts

### Python schemas

The `ucl-open` Python package provides [Pydantic](https://docs.pydantic.dev/) models for every piece of hardware and experiment parameter the platform supports: rig devices, video streams, logging paths, vision stimuli, and so on. Schemas are the source of truth, and define all configurable properties of UclOpen Bonsai operators.

When you run `regenerate.py` in a project scaffolded from the template, those models are compiled to JSON Schema and then to C# classes using [Bonsai.Sgen](https://github.com/bonsai-rx/sgen). Bonsai is then able to read these classes, giving us a common description across Python and Bonsai.

### Bonsai operators

The `UclOpen.*` NuGet packages add Bonsai workflow nodes for:

- **Devices** - Harp devices, cameras, serial hardware
- **Logging** - structured session, CSV, binary, and video logging with BIDS-style paths
- **Video/Vision** - camera configuration and visual stimulus helpers

Operators are configured through externalized properties that map directly to fields in the Pydantic schemas, so a single rig JSON file drives the entire workflow.

### Copier template

Running `copier copy` against the ucl-open template scaffolds a new experiment repository with the right directory layout, a pinned Bonsai environment, a `regenerate.py` pipeline, and deploy scripts. The experimenter fills in the rig and task schemas while the template handles the plumbing and filesystem structure.

## How the parts fit together

1. **`rig.py` / `task.py`** - define devices and experiment parameters as Pydantic models.
2. **`regenerate.py`** - compiles those models to JSON Schema, then to C# classes via Bonsai.Sgen.
3. **`MyProject.Generated.cs`** - the generated classes are committed to the repo; no Python needed on rig machines.
4. **`main.bonsai`** - the workflow loads a rig JSON file at runtime and uses the generated classes to run the experiment.

## Getting started

A complete end-to end tutorial can be found in [Tutorials](../tutorials/introduction.md), which builds a complete experiment from scratch, starting with [Prerequisites](../tutorials/prerequisites.md).
