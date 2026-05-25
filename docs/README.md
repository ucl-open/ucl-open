# ucl-open docs

DocFX site sources for the [ucl-open documentation](https://ucl-open.github.io/ucl-open/).

## Building locally

Workflow SVGs are rendered artefacts - not committed to the repository. Generate them before serving:

```powershell
pwsh docs/build.ps1
dotnet docfx docs/docfx.json --serve
```

`build.ps1` builds the NuGet packages, bootstraps the Bonsai render environment, and writes SVGs into `docs/assets/workflows/` and `docs/workflows/` (both gitignored). DocFX then serves the site at `http://localhost:8080`.

On CI, the `workflow-images` job renders SVGs directly into `artifacts/docs/site/` so they slot into the deployed site without a separate copy step.
