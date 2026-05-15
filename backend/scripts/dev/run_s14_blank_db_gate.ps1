#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [switch]$SkipSync,
    [switch]$KeepRunning,
    [string]$BinDir = "D:\Database\Kingbase\ES\V9\KESRealPro\V009R001C002B0014\Server\bin",
    [string]$RootDir = "D:\Codes\super-ruc-local\kingbase-s14",
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 54324,
    [string]$AdminUser = "sip_admin",
    [string]$AppUser = "sip_user",
    [string]$AppPassword = "sip_pass_dev",
    [string]$AppDatabase = "sip_db",
    [string]$TestDatabase = "sip_db_test",
    [ValidateSet("pg", "postgres", "postgresql", "oracle", "mysql")]
    [string]$DbMode = "pg"
)

$ErrorActionPreference = "Stop"

$bootstrap = Join-Path $PSScriptRoot "bootstrap_local_kingbase.ps1"
$gate = Join-Path $PSScriptRoot "run_s4_kingbase_gate.ps1"
try {
    & $bootstrap -Action reset `
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
    & $bootstrap -Action init `
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

    if ($SkipSync) {
        & $gate -Action migrate -SkipSync `
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
    }
    else {
        & $gate -Action migrate `
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
    }

    & $gate -Action seed -SkipSync `
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

    $env:UV_CACHE_DIR = $config.UvCacheDir
    $env:DATABASE_URL = $config.AppDsn
    $env:KINGBASE_DATABASE_URL = $config.MigrationDsn
    $env:TEST_DATABASE_BOOTSTRAP_URL = $config.BootstrapDsn
    Invoke-CheckedCommand `
        -Executable "uv" `
        -Arguments @("run", "python", "scripts/seed_default_data.py") `
        -Description "uv run python scripts/seed_default_data.py" `
        -WorkingDirectory $config.BackendRoot
}
finally {
    if (-not $KeepRunning) {
        & $bootstrap -Action stop `
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
    }
}
