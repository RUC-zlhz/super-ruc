param(
    [switch]$SkipDocker,
    [switch]$SkipDependencySync,
    [switch]$NoLaunch,
    [int]$BackendPort = 8080,
    [int]$WebPort = 4173
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    return [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
}

function Use-RepoUvCache {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $cacheDir = Join-Path $RepoRoot ".uv-cache-local"
    New-Item -ItemType Directory -Force -Path $cacheDir | Out-Null
    $probe = Join-Path $cacheDir ".write-test"
    Set-Content -LiteralPath $probe -Value "ok" -Encoding ASCII
    Remove-Item -LiteralPath $probe -Force
    $env:UV_CACHE_DIR = $cacheDir
    Write-Host "UV_CACHE_DIR=$env:UV_CACHE_DIR"
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = "",
        [string]$Description = $FilePath
    )

    $pushed = $false
    try {
        if (-not [string]::IsNullOrWhiteSpace($WorkingDirectory)) {
            Push-Location -LiteralPath $WorkingDirectory
            $pushed = $true
        }
        Write-Host "==> $Description"
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$Description failed with exit code $LASTEXITCODE."
        }
    }
    finally {
        if ($pushed) {
            Pop-Location
        }
    }
}

function Wait-TcpPort {
    param(
        [Parameter(Mandatory = $true)]
        [string]$HostName,
        [Parameter(Mandatory = $true)]
        [int]$Port,
        [int]$TimeoutSeconds = 60
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        $client = [System.Net.Sockets.TcpClient]::new()
        try {
            $task = $client.ConnectAsync($HostName, $Port)
            if ($task.Wait(1000) -and $client.Connected) {
                return
            }
        }
        catch {
            Start-Sleep -Milliseconds 500
        }
        finally {
            $client.Dispose()
        }
    }
    throw "Timed out waiting for $HostName`:$Port."
}

function Start-DevTerminal {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [Parameter(Mandatory = $true)]
        [string]$Command
    )

    $escapedTitle = $Title.Replace("'", "''")
    $escapedWorkdir = $WorkingDirectory.Replace("'", "''")
    $escapedCommand = $Command.Replace("'", "''")
    $script = @"
`$Host.UI.RawUI.WindowTitle = '$escapedTitle'
Set-Location -LiteralPath '$escapedWorkdir'
`$env:UV_CACHE_DIR = '$env:UV_CACHE_DIR'
$escapedCommand
Read-Host 'Process exited. Press Enter to close'
"@

    Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        $script
    )
}

$repoRoot = Resolve-RepoRoot
$backendRoot = Join-Path $repoRoot "backend"
$webRoot = Join-Path $repoRoot "web"

Use-RepoUvCache -RepoRoot $repoRoot

$env:APP_ENV = "dev"
$env:APP_DEBUG = "true"
$env:APP_PORT = "$BackendPort"
$env:DATABASE_URL = "postgresql+asyncpg://sip_user:sip_pass_dev@localhost:54322/sip_db"
$env:KINGBASE_DATABASE_URL = $env:DATABASE_URL
$env:REDIS_URL = "redis://:sip_redis_dev@localhost:6379/0"
$env:WECHAT_MOCK_ENABLED = "true"
$env:AUDIT_ARCHIVE_ENABLED = "false"
$env:WORKFLOW_REMINDER_ENABLED = "false"

if (-not $SkipDocker) {
    Invoke-Checked `
        -FilePath "docker" `
        -Arguments @("compose", "-f", (Join-Path $repoRoot "deploy\docker-compose.yml"), "up", "-d") `
        -WorkingDirectory $repoRoot `
        -Description "start local docker services"
    Write-Host "==> wait for local database port"
    Wait-TcpPort -HostName "127.0.0.1" -Port 54322 -TimeoutSeconds 90
}

if (-not $SkipDependencySync) {
    Invoke-Checked `
        -FilePath "uv" `
        -Arguments @("sync", "--extra", "dev") `
        -WorkingDirectory $backendRoot `
        -Description "sync backend dependencies"
}

Invoke-Checked `
    -FilePath "uv" `
    -Arguments @("run", "python", "-m", "scripts.dev.reset_dev_database") `
    -WorkingDirectory $backendRoot `
    -Description "reset development database schema"

Invoke-Checked `
    -FilePath "uv" `
    -Arguments @("run", "alembic", "upgrade", "head") `
    -WorkingDirectory $backendRoot `
    -Description "run database migrations"

Invoke-Checked `
    -FilePath "uv" `
    -Arguments @("run", "python", "-m", "scripts.seed_initial") `
    -WorkingDirectory $backendRoot `
    -Description "seed roles, admin user, policies, dictionaries"

Invoke-Checked `
    -FilePath "uv" `
    -Arguments @("run", "python", "-m", "scripts.seed_default_data") `
    -WorkingDirectory $backendRoot `
    -Description "seed students from xlsx and default curriculum"

if ($NoLaunch) {
    Write-Host ""
    Write-Host "Cold start complete. Server launch skipped."
    exit 0
}

Start-DevTerminal `
    -Title "super-ruc backend :$BackendPort" `
    -WorkingDirectory $backendRoot `
    -Command "uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $BackendPort"

Start-DevTerminal `
    -Title "super-ruc web :$WebPort" `
    -WorkingDirectory $webRoot `
    -Command "pnpm dev --host 0.0.0.0 --port $WebPort"

Write-Host ""
Write-Host "Cold start complete."
Write-Host "Backend: http://localhost:$BackendPort/docs"
Write-Host "Web:     http://localhost:$WebPort"
Write-Host "Admin:   admin / admin123"
