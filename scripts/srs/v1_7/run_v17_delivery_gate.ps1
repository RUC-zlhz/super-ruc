[CmdletBinding()]
param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$uvPrefix = @('run', '--project', 'backend', 'python')
$buildArgs = $uvPrefix + @('scripts/srs/build_srs_v17_from_v16.py')
if ($Force) {
    $buildArgs += '--force'
}

$commands = @(
    ,$buildArgs
    ,($uvPrefix + @('scripts/srs/v1_7/update_v17_docx_split_svg.py'))
    ,($uvPrefix + @('scripts/srs/v1_7/build_v17_emf_variant.py'))
    ,($uvPrefix + @('scripts/srs/v1_7/build_v17_inkscape_emf_variant.py'))
)

Push-Location $repoRoot
try {
    foreach ($commandArgs in $commands) {
        $commandText = "uv $($commandArgs -join ' ')"
        Write-Host $commandText
        & uv @commandArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $commandText"
        }
    }
}
finally {
    Pop-Location
}
