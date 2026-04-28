[CmdletBinding()]
param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$uvPrefix = @('run', '--project', 'backend', 'python')
$buildArgs = $uvPrefix + @('scripts/srs/build_srs_v16_from_v15.py')
if ($Force) {
    $buildArgs += '--force'
}

$commands = @(
    ,$buildArgs
    ,($uvPrefix + @('scripts/srs/v1_6/update_v16_docx_split_svg.py'))
    ,($uvPrefix + @('scripts/srs/v1_6/build_v16_emf_variant.py'))
    ,($uvPrefix + @('scripts/srs/v1_6/build_v16_inkscape_emf_variant.py'))
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
