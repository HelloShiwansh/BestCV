$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run scripts/setup.ps1 first.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot '.env'))) {
    Copy-Item -LiteralPath (Join-Path $projectRoot '.env.example') -Destination (Join-Path $projectRoot '.env')
}
$logDir = Join-Path $projectRoot '.local'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$env:HF_HOME = Join-Path $projectRoot '.cache\huggingface'
$env:PYTHONUTF8 = '1'
$env:PYTHONUNBUFFERED = '1'
$nativeDir = Join-Path $projectRoot '.runtime\weasyprint\_internal'
if ((Test-Path -LiteralPath $nativeDir) -and -not $env:WEASYPRINT_DLL_DIRECTORIES) {
    $env:WEASYPRINT_DLL_DIRECTORIES = $nativeDir
}

foreach ($service in @(
    @{ Name = 'backend'; Port = 8000; Url = 'http://localhost:8000/docs'; Arguments = '-m uvicorn backend.main:app --host 127.0.0.1 --port 8000' },
    @{ Name = 'frontend'; Port = 8501; Url = 'http://localhost:8501'; Arguments = '-m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true' }
)) {
    $processFile = Join-Path $logDir "$($service.Name).process.json"
    $trackedProcess = $null
    if (Test-Path -LiteralPath $processFile) {
        try {
            $savedProcess = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
            $candidate = Get-Process -Id ([int]$savedProcess.id) -ErrorAction SilentlyContinue
            if ($candidate -and $candidate.Path -eq $python -and
                $candidate.StartTime.ToUniversalTime().Ticks -eq $savedProcess.startTimeTicks) {
                $trackedProcess = $candidate
            }
        } catch {
            Write-Warning "Could not read saved $($service.Name) process details; checking its port before starting."
        }
    }
    if ($trackedProcess) {
        Write-Host "$($service.Name) is already running or starting (process $($trackedProcess.Id))."
        Write-Host "$($service.Url) (available when startup completes)"
        continue
    }
    $listener = Get-NetTCPConnection -LocalPort $service.Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        Write-Warning "$($service.Name) was not started: port $($service.Port) is occupied by another process. Close the conflicting application before starting this service."
        continue
    }
    $workingDir = $projectRoot
    if ($service.Name -eq 'frontend') { $workingDir = Join-Path $projectRoot 'frontend' }
    $process = Start-Process -FilePath $python -ArgumentList $service.Arguments -WorkingDirectory $workingDir -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDir "$($service.Name).out.log") -RedirectStandardError (Join-Path $logDir "$($service.Name).err.log")
    @{ id = $process.Id; startTimeTicks = $process.StartTime.ToUniversalTime().Ticks } |
        ConvertTo-Json | Set-Content -LiteralPath $processFile
    Write-Host "$($service.Name) is starting (process $($process.Id))."
    Write-Host "$($service.Url) (available when startup completes)"
}
Write-Host 'Backend model loading may take a minute.'
Write-Host 'Logs: .local/ | Stop: scripts/stop.ps1'
