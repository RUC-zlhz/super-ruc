$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$miniappRoot = Join-Path $repoRoot 'miniapp'
$apiBaseUrl = 'http://123.57.54.195/api/v1'
$outputRequestJs = Join-Path $miniappRoot 'dist\build\mp-weixin\utils\request.js'

$previousApiBaseUrl = $env:VITE_MINIAPP_API_BASE_URL

try {
  $env:VITE_MINIAPP_API_BASE_URL = $apiBaseUrl
  pnpm -C $miniappRoot build:mp-weixin

  if (-not (Test-Path $outputRequestJs)) {
    throw "Miniapp build output not found: $outputRequestJs"
  }

  $containsTempApi = Select-String -Path $outputRequestJs -Pattern ([regex]::Escape($apiBaseUrl)) -Quiet
  if (-not $containsTempApi) {
    throw "Miniapp build output does not contain expected API base URL: $apiBaseUrl"
  }
} finally {
  if ($null -eq $previousApiBaseUrl) {
    Remove-Item Env:\VITE_MINIAPP_API_BASE_URL -ErrorAction SilentlyContinue
  } else {
    $env:VITE_MINIAPP_API_BASE_URL = $previousApiBaseUrl
  }
}
