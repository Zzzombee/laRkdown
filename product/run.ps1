param([Parameter(ValueFromRemainingArguments=$true)][string[]]$ScriptArgs)
$ErrorActionPreference = 'Stop'
try {
    $settings = Get-Content -LiteralPath (Join-Path $PSScriptRoot '.agents/config/runtime.local.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($settings.schema_version -ne 1 -or -not [IO.Path]::IsPathRooted($settings.python) -or -not (Test-Path -LiteralPath $settings.python -PathType Leaf)) { throw 'Selected Python is unavailable; repeat environment preparation.' }
    & $settings.python (Join-Path $PSScriptRoot 'run.py') @ScriptArgs
    exit $LASTEXITCODE
} catch { Write-Error $_.Exception.Message; exit 1 }
