[CmdletBinding()] param (
    [string[]]$docfxArgs
)
Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $true

Push-Location $PSScriptRoot
try {
    $bonsaiDir = Join-Path $PSScriptRoot '.bonsai'
    $bonsaiExe = Join-Path $bonsaiDir 'Bonsai.exe'
    if (-not (Test-Path $bonsaiExe)) {
        Write-Host "Downloading Bonsai bootstrapper..."
        $bonsaiConfig = [xml](Get-Content (Join-Path $bonsaiDir 'Bonsai.config'))
        $bonsaiVersion = ($bonsaiConfig.PackageConfiguration.Packages.Package | Where-Object { $_.id -eq 'Bonsai' }).version
        $downloadUrl = "https://github.com/bonsai-rx/bonsai/releases/download/$bonsaiVersion/Bonsai.zip"
        $tempZip = Join-Path $bonsaiDir 'temp.zip'
        $nugetConfig = Join-Path $bonsaiDir 'NuGet.config'
        $tempNuget = Join-Path $bonsaiDir 'temp.config'
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tempZip
        Move-Item -Path $nugetConfig -Destination $tempNuget -ErrorAction SilentlyContinue
        Expand-Archive -Path $tempZip -DestinationPath $bonsaiDir -Force
        Move-Item -Path $tempNuget -Destination $nugetConfig -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $tempZip
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
