[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# Official WeasyPrint release: the onedir archive includes Pango and its DLLs.
# Keep the URL and digest pinned together when updating the runtime.
$version = '70.0'
$downloadUrl = 'https://github.com/Kozea/WeasyPrint/releases/download/v70.0/weasyprint-windows-onedir.zip'
$expectedHash = 'ab1151f210b4e6bb7aa7a79e91a67e8ddb760094c107bfda55241b6aaefe7d53'
$projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..')).TrimEnd([IO.Path]::DirectorySeparatorChar)
$runtimeRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot '.runtime'))
$installRoot = [IO.Path]::GetFullPath((Join-Path $runtimeRoot 'weasyprint'))
$archivePath = Join-Path $runtimeRoot "weasyprint-windows-onedir-v$version.zip"
$dllRoot = Join-Path $installRoot '_internal'

function Assert-SafeProjectPath([string] $TargetPath) {
    $fullPath = [IO.Path]::GetFullPath($TargetPath)
    $projectPrefix = $projectRoot + [IO.Path]::DirectorySeparatorChar
    if (-not $fullPath.StartsWith($projectPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Runtime path escapes the project folder: $fullPath"
    }

    # Textual containment is insufficient if an existing folder is a junction.
    $cursor = $fullPath
    while ($cursor -and $cursor -ne $projectRoot) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Refusing a runtime path containing a junction or symbolic link: $cursor"
            }
        }
        $cursor = [IO.Path]::GetDirectoryName($cursor)
    }
}

Assert-SafeProjectPath $runtimeRoot
Assert-SafeProjectPath $installRoot
Assert-SafeProjectPath $archivePath
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null

if (-not (Test-Path -LiteralPath $archivePath -PathType Leaf)) {
    Write-Host "Downloading official WeasyPrint $version portable runtime (about 32 MB)..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $downloadUrl -OutFile $archivePath -UseBasicParsing
}

$actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $expectedHash) {
    throw "WeasyPrint archive SHA256 mismatch. Remove '$archivePath' and run this script again."
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::OpenRead($archivePath)
try {
    $entries = [Collections.Generic.List[object]]::new()
    $archivePrefix = 'onedir/weasyprint/'
    $installPrefix = $installRoot + [IO.Path]::DirectorySeparatorChar

    # Validate every destination before extracting any archive entries.
    foreach ($entry in $archive.Entries) {
        $entryName = $entry.FullName.Replace('\', '/')
        if ($entryName -eq 'onedir/' -or $entryName -eq $archivePrefix) {
            continue
        }
        if ($entryName.StartsWith($archivePrefix, [StringComparison]::Ordinal)) {
            $relativePath = $entryName.Substring($archivePrefix.Length)
        }
        elseif ($entryName -eq 'README.rst' -or $entryName -eq 'LICENSE') {
            $relativePath = $entryName
        }
        else {
            throw "Unexpected entry in the pinned WeasyPrint archive: $entryName"
        }
        if ([IO.Path]::IsPathRooted($relativePath) -or $relativePath -match '(^|/)\.\.(/|$)|:') {
            throw "Unsafe path in WeasyPrint archive: $entryName"
        }

        $targetPath = [IO.Path]::GetFullPath((Join-Path $installRoot $relativePath))
        if (-not $targetPath.StartsWith($installPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Archive entry escapes the runtime folder: $entryName"
        }
        Assert-SafeProjectPath $targetPath
        $entries.Add([pscustomobject]@{
            Entry = $entry
            Target = $targetPath
            IsDirectory = $entryName.EndsWith('/')
        })
    }

    foreach ($planned in $entries) {
        if ($planned.IsDirectory) {
            New-Item -ItemType Directory -Path $planned.Target -Force | Out-Null
            continue
        }
        $parentPath = [IO.Path]::GetDirectoryName($planned.Target)
        New-Item -ItemType Directory -Path $parentPath -Force | Out-Null
        $inputStream = $planned.Entry.Open()
        try {
            $outputStream = [IO.File]::Open($planned.Target, [IO.FileMode]::Create, [IO.FileAccess]::Write)
            try {
                $inputStream.CopyTo($outputStream)
            }
            finally {
                $outputStream.Dispose()
            }
        }
        finally {
            $inputStream.Dispose()
        }
    }
}
finally {
    $archive.Dispose()
}

foreach ($library in @('libpango-1.0-0.dll', 'libpangoft2-1.0-0.dll', 'libharfbuzz-0.dll', 'libfontconfig-1.dll', 'libgobject-2.0-0.dll')) {
    if (-not (Test-Path -LiteralPath (Join-Path $dllRoot $library) -PathType Leaf)) {
        throw "The extracted runtime is missing $library"
    }
}

Write-Host "Portable WeasyPrint native libraries are ready at: $dllRoot"
Write-Host 'For a manually started backend, set this variable in the same PowerShell session:'
Write-Host ('$env:WEASYPRINT_DLL_DIRECTORIES = ' + "'$dllRoot'")
Write-Host 'The bundled weasyprint.exe was not executed. No system environment settings were changed.'
