param([string]$PythonExecutable)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $python)) {
    if (-not $PythonExecutable) {
        $candidates = @(
            "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
            'C:\Program Files\Python311\python.exe'
        )
        $PythonExecutable = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    }
    if ($PythonExecutable) {
        & $PythonExecutable -m venv .venv
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.11 -m venv .venv
    } else {
        throw 'Install 64-bit Python 3.11 or pass -PythonExecutable with its full path.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
}

& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Could not update pip. Check your internet connection.' }
& $python -m pip install --no-compile -r requirements.windows.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
& (Join-Path $PSScriptRoot 'setup-pdf-runtime.ps1')
& $python -m spacy download en_core_web_md
if ($LASTEXITCODE -ne 0) { throw 'Could not download the spaCy English model.' }

$env:HF_HOME = Join-Path $projectRoot '.cache\huggingface'
& $python -c "from backend.core.config import SENTENCE_TRANSFORMER_MODEL; from sentence_transformers import SentenceTransformer; SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)"
if ($LASTEXITCODE -ne 0) { throw 'Could not download the sentence model.' }

if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
& $python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Installed dependencies have conflicts.' }
Write-Host 'Dependencies and models are ready. Configure .env and Supabase using README.md, then run scripts/start.ps1.'
