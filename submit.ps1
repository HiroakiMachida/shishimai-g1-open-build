$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$taskSubmission = Get-Content -LiteralPath 'submission.json' -Raw | ConvertFrom-Json
$taskArtifacts = Get-Content -LiteralPath 'dist\artifacts.json' -Raw | ConvertFrom-Json
foreach ($taskFile in @('submission.zip','result.mp4')) {
    $taskActual = (Get-FileHash -LiteralPath (Join-Path 'dist' $taskFile) -Algorithm SHA256).Hash.ToLowerInvariant()
    $taskExpected = $taskArtifacts.files.$taskFile.sha256
    if ($taskActual -ne $taskExpected) { throw "Artifact hash mismatch: $taskFile" }
}
$taskHim = Join-Path $PSScriptRoot '.venv\Scripts\him.exe'
if (!(Test-Path -LiteralPath $taskHim)) { $taskHim = (Get-Command him -ErrorAction Stop).Source }
& $taskHim whoami --json
if ($LASTEXITCODE -ne 0) { throw 'HIM login is required. Run him login and enter the developer token only in its hidden prompt.' }
$taskArguments = @('upload','dist\submission.zip','--video','dist\result.mp4','--kind',$taskSubmission.kind,
    '--robot',$taskSubmission.robot,'--simulator',$taskSubmission.simulator,'--challenge',$taskSubmission.challenge,
    '--name',$taskSubmission.name,'--caption',$taskSubmission.caption,'--run-command',$taskSubmission.run_command,
    '--idempotency-key',$taskArtifacts.upload_idempotency_key,'--yes','--json')
& $taskHim @taskArguments | Tee-Object -FilePath 'dist\publication.json'
if ($LASTEXITCODE -ne 0) { throw 'HIM upload did not complete; keep publication.json and retry with the same artifacts/idempotency key.' }
