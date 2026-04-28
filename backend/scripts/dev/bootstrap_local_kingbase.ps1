#!/usr/bin/env pwsh
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("init", "start", "stop", "reset", "status")]
    [string]$Action = "status",
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

$initDb = Get-KingbaseBinary -Config $config -Name "initdb.exe"
$sysCtl = Get-KingbaseBinary -Config $config -Name "sys_ctl.exe"
$createdb = Get-KingbaseBinary -Config $config -Name "createdb.exe"
$ksql = Get-KingbaseBinary -Config $config -Name "ksql.exe"
$sysIsReady = Get-KingbaseBinary -Config $config -Name "sys_isready.exe"

function Ensure-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Quote-Identifier {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    return '"' + $Value.Replace('"', '""') + '"'
}

function Escape-SqlLiteral {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    return $Value.Replace("'", "''")
}

function Set-MarkedBlock {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$StartMarker,
        [Parameter(Mandatory = $true)]
        [string]$EndMarker,
        [Parameter(Mandatory = $true)]
        [string[]]$Lines
    )

    $block = (@($StartMarker) + $Lines + @($EndMarker)) -join "`r`n"
    $existing = ""
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        $existing = Get-Content -LiteralPath $Path -Raw
    }

    if ($existing.Contains($StartMarker) -and $existing.Contains($EndMarker)) {
        $startIndex = $existing.IndexOf($StartMarker, [System.StringComparison]::Ordinal)
        $endIndex = $existing.IndexOf($EndMarker, $startIndex, [System.StringComparison]::Ordinal)
        if ($endIndex -lt 0) {
            throw "Config marker end not found in $Path"
        }
        $prefix = $existing.Substring(0, $startIndex).TrimEnd("`r", "`n")
        $suffix = $existing.Substring($endIndex + $EndMarker.Length).TrimStart("`r", "`n")
        $parts = @()
        if (-not [string]::IsNullOrWhiteSpace($prefix)) {
            $parts += $prefix
        }
        $parts += $block
        if (-not [string]::IsNullOrWhiteSpace($suffix)) {
            $parts += $suffix
        }
        $updated = $parts -join "`r`n`r`n"
    }
    elseif ([string]::IsNullOrWhiteSpace($existing)) {
        $updated = $block
    }
    else {
        $updated = $existing.TrimEnd() + "`r`n`r`n" + $block
    }

    Set-Content -LiteralPath $Path -Value $updated
}

function Invoke-KsqlScalar {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,
        [string]$Database = $config.BootstrapDatabase
    )

    $args = @(
        "-X",
        "-q",
        "-t",
        "-A",
        "-w",
        "-h", $config.Host,
        "-p", "$($config.Port)",
        "-U", $config.AdminUser,
        "-d", $Database,
        "-c", $Sql
    )

    $output = & $ksql @args
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "ksql scalar query failed with exit code $exitCode. SQL=$Sql"
    }
    return (($output | Out-String).Trim())
}

function Invoke-KsqlNonQuery {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Sql,
        [string]$Database = $config.BootstrapDatabase
    )

    $args = @(
        "-X",
        "-q",
        "-w",
        "-v", "ON_ERROR_STOP=1",
        "-h", $config.Host,
        "-p", "$($config.Port)",
        "-U", $config.AdminUser,
        "-d", $Database,
        "-c", $Sql
    )

    & $ksql @args
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "ksql command failed with exit code $exitCode. SQL=$Sql"
    }
}

function Wait-ForReady {
    param(
        [int]$Attempts = 30,
        [int]$DelaySeconds = 2
    )

    for ($index = 0; $index -lt $Attempts; $index += 1) {
        & $sysIsReady -q -h $config.Host -p $config.Port -d $config.BootstrapDatabase -U $config.AdminUser -t 3 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Start-Sleep -Seconds $DelaySeconds
    }

    throw "Kingbase did not become ready on $($config.Host):$($config.Port) within the expected time."
}

function Ensure-AppRole {
    $escapedRoleName = Escape-SqlLiteral -Value $config.AppUser
    $roleExists = Invoke-KsqlScalar -Sql "SELECT 1 FROM pg_roles WHERE rolname = '$escapedRoleName';"
    $quotedRole = Quote-Identifier -Value $config.AppUser
    $escapedPassword = Escape-SqlLiteral -Value $config.AppPassword

    if ($roleExists -eq "1") {
        Invoke-KsqlNonQuery -Sql "ALTER ROLE $quotedRole LOGIN PASSWORD '$escapedPassword';"
    }
    else {
        Invoke-KsqlNonQuery -Sql "CREATE ROLE $quotedRole LOGIN PASSWORD '$escapedPassword';"
    }
}

function Ensure-DatabaseOwnedByAppUser {
    param(
        [Parameter(Mandatory = $true)]
        [string]$DatabaseName
    )

    $escapedDatabaseName = Escape-SqlLiteral -Value $DatabaseName
    $quotedDatabaseName = Quote-Identifier -Value $DatabaseName
    $quotedRole = Quote-Identifier -Value $config.AppUser
    $existing = Invoke-KsqlScalar -Sql "SELECT 1 FROM pg_database WHERE datname = '$escapedDatabaseName';"

    if ($existing -ne "1") {
        Invoke-CheckedCommand `
            -Executable $createdb `
            -Arguments @(
                "-w",
                "-h", $config.Host,
                "-p", "$($config.Port)",
                "-U", $config.AdminUser,
                "-O", $config.AppUser,
                "--maintenance-db=$($config.BootstrapDatabase)",
                $DatabaseName
            ) `
            -Description "createdb $DatabaseName"
        return
    }

    Invoke-KsqlNonQuery -Sql "ALTER DATABASE $quotedDatabaseName OWNER TO $quotedRole;"
}

function Update-KingbaseConfig {
    if (-not (Test-Path -LiteralPath $config.KingbaseConfigPath -PathType Leaf)) {
        throw "Kingbase config not found: $($config.KingbaseConfigPath)"
    }

    Set-MarkedBlock `
        -Path $config.KingbaseConfigPath `
        -StartMarker "# codex-super-ruc-local-kingbase-runtime begin" `
        -EndMarker "# codex-super-ruc-local-kingbase-runtime end" `
        -Lines @(
            "listen_addresses = '$($config.Host)'",
            "port = $($config.Port)"
        )
}

function Initialize-Cluster {
    Ensure-Directory -Path $config.RootDir
    Ensure-Directory -Path $config.LogDir

    if (Test-KingbaseClusterInitialized -Config $config) {
        Write-Host "Cluster already initialized at $($config.DataDir)"
        return
    }

    if (Test-Path -LiteralPath $config.DataDir) {
        $entries = Get-ChildItem -LiteralPath $config.DataDir -Force -ErrorAction SilentlyContinue
        if ($entries) {
            throw "Data directory exists but is not an initialized cluster: $($config.DataDir). Run reset first."
        }
    }

    Invoke-CheckedCommand `
        -Executable $initDb `
        -Arguments @(
            "-D", $config.DataDir,
            "-U", $config.AdminUser,
            "--auth-host=trust",
            "--auth-local=trust",
            "-E", "UTF8",
            "-m", $config.DbMode
        ) `
        -Description "initdb ($($config.DbMode))"

    Update-KingbaseConfig
}

function Start-Cluster {
    if (-not (Test-KingbaseClusterInitialized -Config $config)) {
        throw "Cluster is not initialized. Run '$PSCommandPath init' first."
    }

    Ensure-Directory -Path $config.LogDir
    if (Test-KingbaseReady -Config $config) {
        Write-Host "Cluster already running on $($config.Host):$($config.Port)"
        return
    }

    Invoke-CheckedCommand `
        -Executable $sysCtl `
        -Arguments @(
            "start",
            "-D", $config.DataDir,
            "-l", $config.LogFile,
            "-w",
            "-t", "120"
        ) `
        -Description "sys_ctl start"

    Wait-ForReady
}

function Stop-Cluster {
    if (-not (Test-KingbaseClusterInitialized -Config $config)) {
        Write-Host "Cluster is not initialized."
        return
    }

    if (-not (Test-KingbaseReady -Config $config)) {
        Write-Host "Cluster is already stopped."
        return
    }

    Invoke-CheckedCommand `
        -Executable $sysCtl `
        -Arguments @(
            "stop",
            "-D", $config.DataDir,
            "-m", "fast",
            "-w",
            "-t", "120"
        ) `
        -Description "sys_ctl stop"
}

function Ensure-AppDatabases {
    Ensure-AppRole
    Ensure-DatabaseOwnedByAppUser -DatabaseName $config.AppDatabase
    Ensure-DatabaseOwnedByAppUser -DatabaseName $config.TestDatabase
}

function Reset-Cluster {
    Assert-SafeRuntimePath -Path $config.DataDir -RootDir $config.RootDir
    Assert-SafeRuntimePath -Path $config.LogDir -RootDir $config.RootDir

    if ((Test-KingbaseClusterInitialized -Config $config) -and (Test-KingbaseReady -Config $config)) {
        Stop-Cluster
    }

    if (Test-Path -LiteralPath $config.DataDir) {
        Remove-Item -LiteralPath $config.DataDir -Recurse -Force
    }
    if (Test-Path -LiteralPath $config.LogDir) {
        Remove-Item -LiteralPath $config.LogDir -Recurse -Force
    }

    Ensure-Directory -Path $config.RootDir
    Write-Host "Removed isolated runtime under $($config.RootDir)"
}

function Show-Status {
    Write-Host "Isolated Kingbase runtime"
    Write-Host "  BinDir:   $($config.BinDir)"
    Write-Host "  RootDir:  $($config.RootDir)"
    Write-Host "  DataDir:  $($config.DataDir)"
    Write-Host "  LogFile:  $($config.LogFile)"
    Write-Host "  Mode:     $($config.DbMode)"
    Write-Host "  HostPort: $($config.Host):$($config.Port)"
    Write-Host "  Init:     $([bool](Test-KingbaseClusterInitialized -Config $config))"

    if (Test-KingbaseClusterInitialized -Config $config) {
        Write-Host ""
        & $sysCtl status -D $config.DataDir
        if ($LASTEXITCODE -ne 0) {
            Write-Host "sys_ctl status: cluster not running"
        }

        $ready = Test-KingbaseReady -Config $config
        Write-Host "  Ready:    $ready"
        if ($ready) {
            $databaseList = Invoke-KsqlScalar `
                -Sql "SELECT string_agg(datname, ', ' ORDER BY datname) FROM pg_database WHERE datname IN ('$($config.AppDatabase)', '$($config.TestDatabase)', '$($config.BootstrapDatabase)');"
            if (-not [string]::IsNullOrWhiteSpace($databaseList)) {
                Write-Host "  Databases: $databaseList"
            }
        }
    }

    Write-KingbaseConnectionSummary -Config $config
}

switch ($Action) {
    "init" {
        Initialize-Cluster
        Start-Cluster
        Ensure-AppDatabases
        Show-Status
    }
    "start" {
        Start-Cluster
        Show-Status
    }
    "stop" {
        Stop-Cluster
        Show-Status
    }
    "reset" {
        Reset-Cluster
        Show-Status
    }
    "status" {
        Show-Status
    }
    default {
        throw "Unsupported action: $Action"
    }
}
