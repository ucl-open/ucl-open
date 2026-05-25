# Developer Setup

## Prerequisites

The following tools are required on Windows 10 or 11 before working with ucl-open projects.

| Tool | Version | Purpose |
|------|---------|---------|
| [Git](https://git-scm.com/) | Any recent | Version control |
| [.NET 8 SDK](https://dotnet.microsoft.com/download/dotnet/8.0) | 8.x | Building C# packages and the DocFX site |
| [Python](https://www.python.org/downloads/) + [`uv`](https://docs.astral.sh/uv/) | 3.13 | Python package, schema generation, tests |
| [Bonsai](https://bonsai-rx.org/) | 2.9 | Running and editing experiment workflows |

## Automated install

The following PowerShell script installs all prerequisites on a fresh Windows machine using `winget`:

```powershell
Write-Host "Installing dependencies..." -ForegroundColor White
$autoaccept = @("--accept-package-agreements", "--accept-source-agreements")

winget install -e --id 7zip.7zip @autoaccept
winget install ffmpeg -v 7.0 @autoaccept
winget install -e --id Git.Git @autoaccept
winget install -e --id Python.Python.3.13 --scope user @autoaccept
winget install -e --id Microsoft.VisualStudioCode --scope user @autoaccept --override '/SILENT /mergetasks="!runcode,addcontextmenufiles,addcontextmenufolders"'
winget install -e --id Microsoft.DotNet.Framework.DeveloperPack_4 @autoaccept
Winget install "Microsoft Visual C++ 2012 Redistributable (x64)" --force @autoaccept
winget install -e --id Nvidia.GeForceExperience @autoaccept
winget install -e --id Nvidia.CUDA -v 11.3 @autoaccept
winget install -e --id Notepad++.Notepad++ @autoaccept
winget install --id=Microsoft.DotNet.SDK.8  -e @autoaccept
winget install --id=astral-sh.uv  -e @autoaccept

## Install dotnet tools

dotnet tool install --global Bonsai.Sgen
dotnet tool install --global Harp.Toolkit

## Install vscode extensions
$extensions =
    "eamodio.gitlens",
    "donjayamanne.python-extension-pack"
    "redhat.vscode-yaml"

$cmd = "code --list-extensions"
Invoke-Expression $cmd -OutVariable output | Out-Null
$installed = $output -split "\s"

foreach ($ext in $extensions) {
    if ($installed.Contains($ext)) {
        Write-Host $ext "already installed." -ForegroundColor Gray
    } else {
        Write-Host "Installing" $ext "..." -ForegroundColor White
        code --install-extension $ext
    }
}
```

## After install

Once the tools are installed, verify the environment for a cloned ucl-open project:

1. **Restore Python dependencies** - `uv sync --extra dev`
2. **Restore .NET tools** - `dotnet tool restore`
3. **Build the .NET packages** - `dotnet build`
4. **Build and preview the docs** - `dotnet docfx docs/docfx.json --serve`
