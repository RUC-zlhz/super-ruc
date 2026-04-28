Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-SuperRucRoot {
    return [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\.."))
}

function Resolve-AbsolutePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    return [System.IO.Path]::GetFullPath($Path)
}

function Normalize-KingbaseDbMode {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DbMode
    )

    switch ($DbMode.ToLowerInvariant()) {
        "postgres" { return "pg" }
        "postgresql" { return "pg" }
        default { return $DbMode.ToLowerInvariant() }
    }
}

function Get-AsyncpgDsn {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ListenHost,
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [Parameter(Mandatory = $true)]
        [string]$Database,
        [Parameter(Mandatory = $true)]
        [string]$User,
        [string]$Password = ""
    )

    $userInfo = [System.Uri]::EscapeDataString($User)
    if (-not [string]::IsNullOrEmpty($Password)) {
        $encodedPassword = [System.Uri]::EscapeDataString($Password)
        $userInfo = "$userInfo`:$encodedPassword"
    }

    return "postgresql+asyncpg://$userInfo@$ListenHost`:$Port/$Database"
}

function Get-KingbaseRuntimeConfig {
    param(
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

    $normalizedDbMode = Normalize-KingbaseDbMode -DbMode $DbMode
    $repoRoot = Resolve-SuperRucRoot
    $backendRoot = [System.IO.Path]::GetFullPath((Join-Path $repoRoot "backend"))
    $resolvedRootDir = Resolve-AbsolutePath -Path $RootDir
    $resolvedBinDir = Resolve-AbsolutePath -Path $BinDir
    $logDir = Join-Path $resolvedRootDir "log"
    $dataDir = Join-Path $resolvedRootDir "data"
    $bootstrapDatabase = "template1"

    $config = [PSCustomObject]@{
        RepoRoot           = $repoRoot
        BackendRoot        = $backendRoot
        BinDir             = $resolvedBinDir
        RootDir            = $resolvedRootDir
        DataDir            = $dataDir
        LogDir             = $logDir
        LogFile            = Join-Path $logDir "kingbase-$Port.log"
        Host               = $ListenHost
        Port               = $Port
        AdminUser          = $AdminUser
        AppUser            = $AppUser
        AppPassword        = $AppPassword
        AppDatabase        = $AppDatabase
        TestDatabase       = $TestDatabase
        BootstrapDatabase  = $bootstrapDatabase
        DbMode             = $normalizedDbMode
        KingbaseConfigPath = Join-Path $dataDir "kingbase.conf"
        UvCacheDir         = Join-Path $repoRoot ".uv-cache"
    }

    $config | Add-Member -NotePropertyName AppDsn -NotePropertyValue (
        Get-AsyncpgDsn -ListenHost $config.Host -Port $config.Port -Database $config.AppDatabase -User $config.AppUser -Password $config.AppPassword
    )
    $config | Add-Member -NotePropertyName TestDsn -NotePropertyValue (
        Get-AsyncpgDsn -ListenHost $config.Host -Port $config.Port -Database $config.TestDatabase -User $config.AppUser -Password $config.AppPassword
    )
    $config | Add-Member -NotePropertyName MigrationDsn -NotePropertyValue $config.AppDsn
    $config | Add-Member -NotePropertyName BootstrapDsn -NotePropertyValue (
        Get-AsyncpgDsn -ListenHost $config.Host -Port $config.Port -Database $config.BootstrapDatabase -User $config.AdminUser
    )

    return $config
}

function Get-KingbaseBinary {
    param(
        [Parameter(Mandatory = $true)]
        $Config,
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $path = Join-Path $Config.BinDir $Name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Kingbase binary not found: $path"
    }
    return $path
}

function Test-KingbaseClusterInitialized {
    param(
        [Parameter(Mandatory = $true)]
        $Config
    )

    return (Test-Path -LiteralPath $Config.KingbaseConfigPath -PathType Leaf)
}

function Test-KingbaseReady {
    param(
        [Parameter(Mandatory = $true)]
        $Config
    )

    $sysIsReady = Get-KingbaseBinary -Config $Config -Name "sys_isready.exe"
    & $sysIsReady -q -h $Config.Host -p $Config.Port -d $Config.BootstrapDatabase -U $Config.AdminUser -t 3 | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,
        [string[]]$Arguments = @(),
        [string]$Description = $Executable,
        [string]$WorkingDirectory = ""
    )

    $pushed = $false
    try {
        if (-not [string]::IsNullOrEmpty($WorkingDirectory)) {
            Push-Location -LiteralPath $WorkingDirectory
            $pushed = $true
        }

        Write-Host "==> $Description"
        & $Executable @Arguments
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            throw "$Description failed with exit code $exitCode."
        }
    }
    finally {
        if ($pushed) {
            Pop-Location
        }
    }
}

function Assert-SafeRuntimePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$RootDir
    )

    $fullPath = Resolve-AbsolutePath -Path $Path
    $fullRoot = Resolve-AbsolutePath -Path $RootDir
    $prefix = "$fullRoot\"
    if ($fullPath -ne $fullRoot -and -not $fullPath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside runtime root. Path=$fullPath Root=$fullRoot"
    }
}

function Write-KingbaseConnectionSummary {
    param(
        [Parameter(Mandatory = $true)]
        $Config
    )

    Write-Host ""
    Write-Host "Connection settings"
    Write-Host "  DATABASE_URL=$($Config.AppDsn)"
    Write-Host "  KINGBASE_DATABASE_URL=$($Config.MigrationDsn)"
    Write-Host "  TEST_DATABASE_BOOTSTRAP_URL=$($Config.BootstrapDsn)"
    Write-Host "  TEST_DATABASE_URL=$($Config.TestDsn)"
    Write-Host ""
}
