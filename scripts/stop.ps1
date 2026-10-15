$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$expectedPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
foreach ($name in @('frontend', 'backend')) {
    $processFile = Join-Path $projectRoot ".local\$name.process.json"
    if (-not (Test-Path -LiteralPath $processFile)) { continue }
    try {
        $savedProcess = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
        $process = Get-Process -Id ([int]$savedProcess.id) -ErrorAction SilentlyContinue
        if ($process) {
            if ($process.Path -eq $expectedPython -and
                $process.StartTime.ToUniversalTime().Ticks -eq $savedProcess.startTimeTicks) {
                # Windows virtual environments use a launcher and a child Python process.
                & taskkill.exe /PID $process.Id /T /F | Out-Null
                if ($LASTEXITCODE -ne 0) { throw "Could not stop process $($process.Id)." }
                Write-Host "$name stopped."
            } else {
                Write-Warning "Skipped process $($savedProcess.id) because its path or start time does not match the saved $name process."
            }
        }
    } catch {
        Write-Warning "Could not verify or stop the saved $name process: $($_.Exception.Message)"
        continue
    }
    Remove-Item -LiteralPath $processFile
}
