#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("migrate", "seed", "tests", "benchmark", "all")]
    [string]$Action = "all",
    [switch]$SkipSync,
    [string]$BinDir = "D:\Database\Kingbase\ES\V9\KESRealPro\V009R001C002B0014\Server\bin",
    [string]$RootDir = "D:\Codes\super-ruc-local\kingbase-s4",
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 54323,
    [string]$AdminUser = "sip_admin",
    [string]$AppUser = "sip_user",
    [string]$AppPassword = "sip_pass_dev",
    [string]$AppDatabase = "sip_db",
    [string]$TestDatabase = "sip_db_test",
    [ValidateSet("pg", "postgres", "postgresql", "oracle", "mysql")]
    [string]$DbMode = "pg"
)

. (Join-Path $PSScriptRoot "common.ps1")

$config = Get-KingbaseRuntimeConfig `
    -BinDir $BinDir `
    -RootDir $RootDir `
    -ListenHost $ListenHost `
    -Port $Port `
    -AdminUser $AdminUser `
    -AppUser $AppUser `
    -AppPassword $AppPassword `
    -AppDatabase $AppDatabase `
    -TestDatabase $TestDatabase `
    -DbMode $DbMode

$testFiles = @(
    "tests/integration/test_audit_runtime.py",
    "tests/integration/test_audit_flow.py",
    "tests/integration/test_auth_flow.py",
    "tests/integration/test_exchange_flow.py",
    "tests/integration/test_honor_flow.py",
    "tests/integration/test_notice_flow.py",
    "tests/integration/test_profile_flow.py",
    "tests/integration/test_report_contract_flow.py",
    "tests/integration/test_request_flow.py",
    "tests/integration/test_smoke.py",
    "tests/integration/test_workflow_party_flow.py"
)

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Assert-RuntimeReady {
    if (-not (Test-KingbaseClusterInitialized -Config $config)) {
        throw "Local Kingbase runtime is not initialized. Run .\backend\scripts\dev\bootstrap_local_kingbase.ps1 init first."
    }
    if (-not (Test-KingbaseReady -Config $config)) {
        throw "Local Kingbase runtime is not running. Run .\backend\scripts\dev\bootstrap_local_kingbase.ps1 start first."
    }
}

function Set-GateEnvironment {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("migrate", "seed", "tests", "benchmark")]
        [string]$Step
    )

    Ensure-Directory -Path $config.UvCacheDir
    $env:UV_CACHE_DIR = $config.UvCacheDir
    $env:TEST_DATABASE_BOOTSTRAP_URL = $config.BootstrapDsn
    $env:KINGBASE_DATABASE_URL = $config.MigrationDsn

    switch ($Step) {
        "migrate" { $env:DATABASE_URL = $config.AppDsn }
        "seed" { $env:DATABASE_URL = $config.AppDsn }
        "tests" { $env:DATABASE_URL = $config.TestDsn }
        "benchmark" { $env:DATABASE_URL = $config.TestDsn }
        default { throw "Unsupported step environment: $Step" }
    }

    Write-Host ""
    Write-Host "Environment for $Step"
    Write-Host "  UV_CACHE_DIR=$($env:UV_CACHE_DIR)"
    Write-Host "  DATABASE_URL=$($env:DATABASE_URL)"
    Write-Host "  KINGBASE_DATABASE_URL=$($env:KINGBASE_DATABASE_URL)"
    Write-Host "  TEST_DATABASE_BOOTSTRAP_URL=$($env:TEST_DATABASE_BOOTSTRAP_URL)"
    Write-Host ""
}

function Invoke-Uv {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    Invoke-CheckedCommand -Executable "uv" -Arguments $Arguments -Description $Description -WorkingDirectory $config.BackendRoot
}

function Invoke-S4Step {
    param(
        [Parameter(Mandatory = $true)]
        [ValidateSet("migrate", "seed", "tests", "benchmark")]
        [string]$Step
    )

    Set-GateEnvironment -Step $Step

    switch ($Step) {
        "migrate" {
            Invoke-Uv -Arguments @("run", "alembic", "upgrade", "head") -Description "uv run alembic upgrade head"
        }
        "seed" {
            Invoke-Uv -Arguments @("run", "python", "scripts/seed_initial.py") -Description "uv run python scripts/seed_initial.py"
        }
        "tests" {
            Invoke-Uv -Arguments (@("run", "pytest") + $testFiles + @("-q")) -Description "uv run pytest (S4 integration gate)"
        }
        "benchmark" {
            Invoke-Uv `
                -Arguments @("run", "pytest", "tests/performance/test_student_import_benchmark.py", "-q", "-s") `
                -Description "uv run pytest tests/performance/test_student_import_benchmark.py -q -s"
        }
        default {
            throw "Unsupported step: $Step"
        }
    }
}

Assert-RuntimeReady
Write-KingbaseConnectionSummary -Config $config

if (-not $SkipSync) {
    Ensure-Directory -Path $config.UvCacheDir
    $env:UV_CACHE_DIR = $config.UvCacheDir
    Invoke-Uv -Arguments @("sync", "--extra", "dev") -Description "uv sync --extra dev"
}

$steps = if ($Action -eq "all") {
    @("migrate", "seed", "tests", "benchmark")
}
else {
    @($Action)
}

foreach ($step in $steps) {
    Invoke-S4Step -Step $step
}
