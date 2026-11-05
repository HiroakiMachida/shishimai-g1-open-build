$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (Test-Path -LiteralPath '.simenv\Scripts\python.exe') { $taskPython = Join-Path $PSScriptRoot '.simenv\Scripts\python.exe' } else { $taskPython = 'python' }
& $taskPython tests/test_policy.py
if ($LASTEXITCODE) { throw 'Policy contract checks failed' }
& $taskPython tests/test_policy.py --benchmark
if ($LASTEXITCODE) { throw 'Task/causality checks failed' }
& $taskPython run.py --seed 1000 --render
if ($LASTEXITCODE) { throw 'Episode/video generation failed' }
