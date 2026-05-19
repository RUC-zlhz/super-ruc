$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$apiBaseUrl = "http://10.10.0.13/api/v1"

Push-Location $repoRoot
try {
    $env:VITE_MINIAPP_API_BASE_URL = $apiBaseUrl
    pnpm -C miniapp build:mp-weixin

    $requestBundle = Join-Path $repoRoot "miniapp\dist\build\mp-weixin\utils\request.js"
    if (-not (Test-Path $requestBundle)) {
        throw "Missing generated request bundle: $requestBundle"
    }
    $content = Get-Content -Raw -Path $requestBundle
    if (-not $content.Contains($apiBaseUrl)) {
        throw "Generated miniapp bundle does not contain $apiBaseUrl"
    }
    Write-Host "miniapp mp-weixin build uses $apiBaseUrl"
}
finally {
    Pop-Location
}
