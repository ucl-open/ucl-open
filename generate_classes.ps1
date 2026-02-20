Set-Location $PSScriptRoot
$env:PYTHONPATH = "$PSScriptRoot\src;$env:PYTHONPATH"
python .\experiment.py
dotnet bonsai.sgen TestExperiment.json -o Extensions --serializer yaml