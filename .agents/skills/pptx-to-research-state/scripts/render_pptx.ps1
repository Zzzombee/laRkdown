param(
    [Parameter(Mandatory = $true)]
    [string]$InputPath,

    [Parameter(Mandatory = $true)]
    [string]$OutputDir,

    [int]$Width = 1920,
    [int]$Height = 1080
)

$ErrorActionPreference = "Stop"
$resolvedInput = (Resolve-Path -LiteralPath $InputPath).Path
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputDir)
[System.IO.Directory]::CreateDirectory($resolvedOutput) | Out-Null

$powerPoint = $null
$presentation = $null
try {
    $powerPoint = New-Object -ComObject PowerPoint.Application
    $presentation = $powerPoint.Presentations.Open($resolvedInput, $true, $false, $false)
    $presentation.Export($resolvedOutput, "PNG", $Width, $Height)
    $expected = $presentation.Slides.Count
}
finally {
    if ($null -ne $presentation) {
        $presentation.Close()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($presentation) | Out-Null
    }
    if ($null -ne $powerPoint) {
        $powerPoint.Quit()
        [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($powerPoint) | Out-Null
    }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}

$actual = (Get-ChildItem -LiteralPath $resolvedOutput -File -Filter '*.PNG').Count
if ($actual -ne $expected) {
    throw "PowerPoint exported $actual slides; expected $expected."
}
Write-Output "Exported $actual slides to $resolvedOutput"
