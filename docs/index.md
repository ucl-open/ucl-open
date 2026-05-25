# ucl-open

ucl-open is an open-source platform for building reproducible neuroscience experiment rigs. It provides shared Python schemas, .NET/Bonsai acquisition operators, and a project template that work together to standardise how rig hardware, task parameters, and experimental data are defined and recorded across a lab.

## Platform components

- **Python schemas** (`ucl-open` package) — [Pydantic](https://docs.pydantic.dev/) models for rig hardware, devices, video, vision, and logging. These are the single source of truth for all experiment parameters and generate matching C# classes for use in Bonsai workflows.
- **.NET/Bonsai operators** (`UclOpen.*` NuGet packages) — Bonsai workflow components for device control, data acquisition, and logging that consume the generated schemas at runtime.
- **Copier template** — a project template that scaffolds a new experiment repository pre-wired with the ucl-open packages, a schema regeneration pipeline, and deployment scripts.

## How it works

Experiment parameters are defined as Pydantic models in Python. A `regenerate` step compiles those models to JSON Schema and then to C# classes via [Bonsai.Sgen](https://github.com/bonsai-rx/sgen). The resulting classes are loaded by the Bonsai workflow at runtime, giving the experiment structured, validated access to rig and task configurations.

## Get started

New to the platform? The [Documentation](articles/introduction.md) section explains how the pieces fit together, and the [Tutorials](tutorials/introduction.md) walk through setting up a complete experiment from scratch.
