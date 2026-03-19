# Test environment

Run the deploy script from the repo root to set up the full development environment.

Double-click `scripts/deploy.cmd`, or run from a terminal:

```
./scripts/deploy.cmd
```

This will:
1. Restore .NET tools
2. Build UclOpen NuGet packages
3. Bootstrap the Bonsai environment and install all packages
4. Install the Python environment via `uv`
5. Generate the experiment schema (`test/local/`) and C# serialisation classes (`test/Extensions/`)

Once complete, launch Bonsai with:

```powershell
./.bonsai/Bonsai.exe
```
