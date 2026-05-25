[CmdletBinding()] param (
    [string[]]$docfxArgs
)
Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

Push-Location $PSScriptRoot
try {
    $bonsaiExe = Join-Path $PSScriptRoot '.bonsai\Bonsai.exe'
    if (-not (Test-Path $bonsaiExe)) {
        Write-Host "Downloading Bonsai bootstrapper..."
        $bonsaiConfig = [xml](Get-Content (Join-Path $PSScriptRoot '.bonsai\Bonsai.config'))
        $bonsaiVersion = ($bonsaiConfig.PackageConfiguration.Packages.Package | Where-Object { $_.id -eq 'Bonsai' }).version
        $downloadUrl = "https://github.com/bonsai-rx/bonsai/releases/download/$bonsaiVersion/Bonsai.exe"
        Invoke-WebRequest -Uri $downloadUrl -OutFile $bonsaiExe
    }
    Write-Host "Bootstrapping Bonsai environment..."
    & $bonsaiExe --no-editor

    $libPaths = @()
    $libPaths += Get-ChildItem "..\artifacts\bin\*\release_net4*" -Directory | Select-Object -Expand FullName
    $libPaths += "..\artifacts\package\release"

    ./export-images.ps1 $libPaths
    dotnet docfx metadata
    dotnet docfx build $docfxArgs
} finally {
    Pop-Location
}
