# ucl-open-rigs

Standard, shareable descriptions of experimental rigs for the ucl-open ecosystem.

---

## Regenerating packages

### 1. Regenerate the PyRAT JSON schema (Python → JSON)

Run whenever `SessionConfig` or any model in `src/ucl_open/pyrat/` changes to generate the JSON classes:

```bash
uv run python src/ucl_open/_generators/session_schema.py
```
---
### 2. Regenerate the C# Bonsai types (JSON → C#)

Run after step 1 to update the generated C# classes into the bonsai package:

```bash
dotnet bonsai.sgen src/ucl_open/schemas/pyrat_session.json --namespace UclOpen.Pyrat -o src/UclOpen.Pyrat --serializer json
```
---
### 3. Repack the NuGet packages

Run after step 2 to publish all updated packages to the local Bonsai feed:

```bash
dotnet pack UclOpen.sln -c Release
```

Or individually if only one package changed:

```bash
dotnet pack src/UclOpen.Core/UclOpen.Core.csproj       -c Release
dotnet pack src/UclOpen.Devices/UclOpen.Devices.csproj -c Release
dotnet pack src/UclOpen.Logging/UclOpen.Logging.csproj -c Release
dotnet pack src/UclOpen.Video/UclOpen.Video.csproj     -c Release
dotnet pack src/UclOpen.Vision/UclOpen.Vision.csproj   -c Release
dotnet pack src/UclOpen.Pyrat/UclOpen.Pyrat.csproj     -c Release
```

Output: `artifacts/package/release/*.nupkg`

Configure local Bonsai config (`.bonsai/NuGet.config`) to pick up packages from that folder.

```bash 
<add key="UclOpen" value="../artifacts/package/release" />
```