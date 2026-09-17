<#
.SYNOPSIS
Runs MatrixWriterRepro.bonsai and reports how much of the expected data was actually written.

.DESCRIPTION
Demonstrates data loss in Bonsai.Dsp.MatrixWriter. The workflow demultiplexes a completing source
into one group per element, each of which opens its own MatrixWriter, and writes a single Int32 to
each. Every run should therefore produce exactly Count files of four bytes each. In practice most
of the files are never written, because Bonsai.IO.StreamSink schedules writer creation, writes and
disposal on a per-writer EventLoopScheduler which is torn down as soon as the sequence completes.

Requires only Bonsai.Core and Bonsai.Dsp. Nothing from this repository is loaded.

.PARAMETER BonsaiExecutable
Path to Bonsai.exe. If omitted, a .bonsai environment beside the repository or the current folder
is used, falling back to bonsai on PATH.

.PARAMETER Count
Number of records to write. One file is expected per record.

.PARAMETER Repeats
How many times to run the workflow. The fault is intermittent, so more runs give a clearer picture.

.EXAMPLE
./Run-MatrixWriterRepro.ps1
Runs the default sweep and prints a summary.

.EXAMPLE
./Run-MatrixWriterRepro.ps1 -Count 50 -Repeats 20 -BonsaiExecutable C:\Bonsai\Bonsai.exe
Runs twenty times against a specific Bonsai install.
#>
[CmdletBinding()]
param (
    [string]$BonsaiExecutable,
    [string]$Workflow = (Join-Path $PSScriptRoot 'MatrixWriterRepro.bonsai'),
    [int]$Count = 50,
    [int]$Repeats = 5,
    [string]$OutputPath = (Join-Path ([System.IO.Path]::GetTempPath()) 'MatrixWriterRepro'),
    [switch]$KeepFiles
)

Set-StrictMode -Version 3.0
$ErrorActionPreference = 'Stop'

# Each record written is a single Int32.
$BytesPerRecord = 4

function Resolve-Bonsai {
    param([string]$Explicit)

    if ($Explicit) {
        if (-not (Test-Path $Explicit)) { throw "Bonsai executable not found at '$Explicit'." }
        return (Resolve-Path $Explicit).Path
    }

    $candidates = @(
        (Join-Path $PSScriptRoot '../../.bonsai/Bonsai.exe'),
        (Join-Path (Get-Location) '.bonsai/Bonsai.exe')
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return (Resolve-Path $candidate).Path }
    }

    $onPath = Get-Command 'bonsai' -ErrorAction SilentlyContinue
    if ($onPath) { return $onPath.Source }

    throw "Could not locate Bonsai.exe. Pass -BonsaiExecutable with the path to your Bonsai install."
}

$bonsai = Resolve-Bonsai -Explicit $BonsaiExecutable
if (-not (Test-Path $Workflow)) { throw "Workflow not found at '$Workflow'." }
$Workflow = (Resolve-Path $Workflow).Path

Write-Verbose "Bonsai:   $bonsai"
Write-Verbose "Workflow: $Workflow"

$null = New-Item -ItemType Directory -Path $OutputPath -Force
$results = @()

foreach ($run in 1..$Repeats) {
    $runPath = Join-Path $OutputPath "run-$run"
    if (Test-Path $runPath) { Remove-Item $runPath -Recurse -Force }
    $null = New-Item -ItemType Directory -Path $runPath -Force

    Write-Verbose "Run $run of $Repeats"
    $arguments = @(
        $Workflow
        '--no-editor'
        '-p', "Path=$runPath"
        '-p', "Count=$Count"
    )

    # Bonsai reports a zero exit code even when a workflow fails to build, so the captured error
    # output is the only reliable signal that something went wrong.
    $errorPath = Join-Path $runPath 'bonsai.err'
    $null = & $bonsai $arguments 2>$errorPath
    if (Test-Path $errorPath) {
        $errorText = (Get-Content $errorPath -Raw)
        if (-not [string]::IsNullOrWhiteSpace($errorText)) {
            Write-Warning "Run ${run}:`n$errorText"
        }
    }

    $files = @(Get-ChildItem $runPath -Recurse -File -Filter *.bin -ErrorAction SilentlyContinue)
    $bytes = ($files | Measure-Object -Property Length -Sum).Sum
    if ($null -eq $bytes) { $bytes = 0 }

    $results += [pscustomobject]@{
        Run             = $run
        ExpectedFiles   = $Count
        ActualFiles     = $files.Count
        ExpectedSamples = $Count
        ActualSamples   = [int]($bytes / $BytesPerRecord)
        Complete        = ($files.Count -eq $Count -and $bytes -eq $Count * $BytesPerRecord)
    }

    if (-not $KeepFiles) { Remove-Item $runPath -Recurse -Force }
}

$results | Format-Table Run, ExpectedFiles, ActualFiles, ExpectedSamples, ActualSamples, Complete -AutoSize | Out-Host

$complete = @($results | Where-Object Complete).Count
$totalExpected = $Count * $Repeats
$totalActual = ($results | Measure-Object -Property ActualSamples -Sum).Sum
if ($null -eq $totalActual) { $totalActual = 0 }

"Complete runs : {0} of {1}" -f $complete, $Repeats | Out-Host
"Samples written: {0} of {1} ({2:P1})" -f $totalActual, $totalExpected, ($totalActual / $totalExpected) | Out-Host

if ($complete -eq $Repeats) {
    "All runs wrote the expected data; the fault did not reproduce." | Out-Host
} else {
    "MatrixWriter discarded data in {0} of {1} runs." -f ($Repeats - $complete), $Repeats | Out-Host
}

if ($KeepFiles) { "Files kept under: $OutputPath" | Out-Host }

if ($complete -ne $Repeats) { exit 1 }
exit 0
