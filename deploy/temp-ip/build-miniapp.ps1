param(
  [string]$ApiBaseUrl = 'http://123.57.54.195/api/v1'
)

$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$miniappRoot = Join-Path $repoRoot 'miniapp'
$outputRoot = Join-Path $miniappRoot 'dist\build\mp-weixin'
$outputRequestJs = Join-Path $outputRoot 'utils\request.js'
$outputProjectConfig = Join-Path $outputRoot 'project.config.json'

function Assert-ChildPath {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [Parameter(Mandatory = $true)]
    [string]$Parent
  )

  $fullPath = [System.IO.Path]::GetFullPath($Path)
  $fullParent = [System.IO.Path]::GetFullPath($Parent)
  if ($fullPath -ne $fullParent -and -not $fullPath.StartsWith("$fullParent\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to operate outside $fullParent`: $fullPath"
  }
}

$previousApiBaseUrl = $env:VITE_MINIAPP_API_BASE_URL

try {
  Assert-ChildPath -Path $outputRoot -Parent $miniappRoot
  if (Test-Path -LiteralPath $outputRoot) {
    Remove-Item -LiteralPath $outputRoot -Recurse -Force
  }

  $env:VITE_MINIAPP_API_BASE_URL = $ApiBaseUrl
  pnpm -C $miniappRoot build:mp-weixin

  if (-not (Test-Path $outputRequestJs)) {
    throw "Miniapp build output not found: $outputRequestJs"
  }
  if (-not (Test-Path $outputProjectConfig)) {
    throw "Miniapp project config not found: $outputProjectConfig"
  }

  $containsTempApi = Select-String -Path $outputRequestJs -Pattern ([regex]::Escape($ApiBaseUrl)) -Quiet
  if (-not $containsTempApi) {
    throw "Miniapp build output does not contain expected API base URL: $ApiBaseUrl"
  }

  $containsEnvKey = Select-String -Path $outputRequestJs -Pattern 'VITE_MINIAPP_API_BASE_URL' -Quiet
  if (-not $containsEnvKey) {
    throw "Miniapp build output does not carry VITE_MINIAPP_API_BASE_URL; runtime may fall back to local default."
  }

  $projectConfigText = Get-Content -LiteralPath $outputProjectConfig -Raw
  if ($projectConfigText -notmatch 'wxcb6352a74505bc41') {
    throw "Miniapp project config does not contain the expected AppID."
  }
} finally {
  if ($null -eq $previousApiBaseUrl) {
    Remove-Item Env:\VITE_MINIAPP_API_BASE_URL -ErrorAction SilentlyContinue
  } else {
    $env:VITE_MINIAPP_API_BASE_URL = $previousApiBaseUrl
  }
}
