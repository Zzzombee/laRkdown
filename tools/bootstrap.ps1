param(
    [string]$Project = (Join-Path (Split-Path $PSScriptRoot -Parent) 'laRkdown'),
    [ValidateSet('core','base','pptx')][string]$Feature = 'core',
    [string]$Python = '',
    [string]$Cache = (Join-Path $env:LOCALAPPDATA 'laRkdown')
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Test-Python([string]$Executable) {
    if (-not $Executable) { return $null }
    try {
        $result = & $Executable -I -c 'import sys,ssl,xml.etree.ElementTree; assert (3,11)<=sys.version_info[:2]<(3,15); print(sys.executable)' 2>$null
        if ($LASTEXITCODE -eq 0) { return ($result | Select-Object -Last 1).Trim() }
    } catch { }
    return $null
}

try {
    $Project = [IO.Path]::GetFullPath($Project)
    $Cache = [IO.Path]::GetFullPath($Cache)
    # Reject the development checkout before any download or project mutation.
    foreach ($candidate in @($Project, (Split-Path $Project -Parent))) {
        if (Test-Path -LiteralPath (Join-Path $candidate 'tools/build_release.py')) { throw 'Use an extracted research directory, not the development checkout.' }
    }
    if (-not (Test-Path -LiteralPath (Join-Path $Project 'run.py'))) { throw 'Extract the research package before preparing its environment.' }
    $layout = Get-Content -LiteralPath (Join-Path $Project '.agents/config/project-layout.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($layout.workspace_kind -ne 'personal-research') { throw 'Unsupported research directory.' }
    $candidates = @()
    if ($Python) { $candidates += $Python }
    $receipt = Join-Path $Project '.agents/config/runtime.local.json'
    if (Test-Path -LiteralPath $receipt) {
        $candidates += (Get-Content -LiteralPath $receipt -Raw -Encoding UTF8 | ConvertFrom-Json).python
    }
    foreach ($name in @('python','python3')) {
        $found = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue
        if ($found -and $found.Source -notlike '*\Microsoft\WindowsApps\*') { $candidates += $found.Source }
    }
    # Registry discovery also works when the current client inherited an old PATH.
    foreach ($registry in @('HKCU:\Software\Python\PythonCore','HKLM:\Software\Python\PythonCore')) {
        if (Test-Path $registry) {
            foreach ($version in Get-ChildItem $registry) {
                $key = Join-Path $version.PSPath 'InstallPath'
                if (Test-Path $key) {
                    $props = Get-ItemProperty $key
                    if ($props.ExecutablePath) { $candidates += $props.ExecutablePath }
                }
            }
        }
    }
    $selected = $null
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        $selected = Test-Python $candidate
        if ($selected) { break }
    }
    if (-not $selected) {
        $arch = [Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
        if ($arch -eq 'x64') { $arch = 'amd64' }
        $assets = Import-Csv -LiteralPath (Join-Path $PSScriptRoot 'runtime-assets.tsv') -Delimiter "`t"
        $asset = $assets | Where-Object { $_.component -eq 'uv' -and $_.platform -eq "windows-$arch" }
        if (-not $asset -or $asset.sha256 -notmatch '^[a-f0-9]{64}$' -or $asset.url -notlike 'https://github.com/astral-sh/uv/releases/download/*') { throw 'No reviewed bootstrap asset for this architecture.' }
        $folder = Join-Path $Cache "bootstrap/uv-$($asset.version)-windows-$arch"
        foreach ($path in @($Cache, (Join-Path $Cache 'bootstrap'), $folder)) {
            if ((Test-Path -LiteralPath $path) -and ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Linked runtime caches are unsupported.' }
        }
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
        $archive = Join-Path $folder 'uv.zip'
        if (-not (Test-Path -LiteralPath $archive)) {
            $part = Join-Path $folder ([Guid]::NewGuid().ToString('N') + '.part')
            try {
                Invoke-WebRequest -Uri $asset.url -OutFile $part -TimeoutSec 120 -UseBasicParsing
                if ((Get-FileHash -LiteralPath $part -Algorithm SHA256).Hash.ToLowerInvariant() -ne $asset.sha256) { throw 'Bootstrap archive checksum mismatch.' }
                Move-Item -LiteralPath $part -Destination $archive
            } finally { if (Test-Path -LiteralPath $part) { Remove-Item -LiteralPath $part } }
        }
        if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $asset.sha256) { throw 'Cached bootstrap archive changed; preserve and inspect it.' }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $zip = [IO.Compression.ZipFile]::OpenRead($archive)
        try {
            $entries = @($zip.Entries | Where-Object { $_.Name -eq 'uv.exe' })
            if ($entries.Count -ne 1) { throw 'Unexpected bootstrap archive.' }
            $uv = Join-Path $folder 'uv.exe'
            $stream = $entries[0].Open()
            $memory = New-Object IO.MemoryStream
            try { $stream.CopyTo($memory); $bytes = $memory.ToArray() } finally { $stream.Dispose(); $memory.Dispose() }
            if (Test-Path -LiteralPath $uv) {
                $actual = [IO.File]::ReadAllBytes($uv)
                $hasher = [Security.Cryptography.SHA256]::Create()
                try {
                    if ([Convert]::ToBase64String($hasher.ComputeHash($actual)) -ne [Convert]::ToBase64String($hasher.ComputeHash($bytes))) { throw 'Cached bootstrap executable changed.' }
                } finally { $hasher.Dispose() }
            } else { [IO.File]::WriteAllBytes($uv, $bytes) }
        } finally { $zip.Dispose() }
        $env:UV_PYTHON_INSTALL_DIR = Join-Path $Cache 'python'
        $env:UV_PYTHON_INSTALL_BIN = '0'
        $env:UV_PYTHON_INSTALL_REGISTRY = '0'
        $env:UV_NO_PROGRESS = '1'
        $env:UV_NO_CONFIG = '1'
        $version = ($assets | Where-Object { $_.component -eq 'python' }).version
        & $uv python install $version --no-bin --no-registry 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Managed Python download failed; retry this entry to resume.' }
        $managed = & $uv python find --managed-python $version
        if ($LASTEXITCODE -ne 0) { throw 'Managed Python was not found.' }
        $selected = Test-Python (($managed | Select-Object -Last 1).Trim())
        if (-not $selected) { throw 'Managed Python did not pass the local check.' }
    }
    & $selected (Join-Path $PSScriptRoot 'setup_larkdown.py') --project $Project --feature $Feature --python $selected --cache $Cache
    exit $LASTEXITCODE
} catch {
    [Console]::Error.WriteLine(('Environment preparation stopped: ' + $_.Exception.Message))
    exit 1
}
