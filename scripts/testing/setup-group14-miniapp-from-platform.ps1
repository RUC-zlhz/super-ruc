param(
    [string]$BaseUrl = "http://183.174.61.212:8001",
    [string]$Username = "",
    [int]$TesteeId = 14,
    [int]$Phase = 1,
    [string]$OutputDir = "tmp/docs/group14/platform-documents",
    [string]$ProjectOutputDir = "tmp/group14-miniapp",
    [switch]$RegisterIfMissing,
    [switch]$ClearClipboardAfterRead
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function Invoke-JsonRequest {
    param(
        [Parameter(Mandatory = $true)] [string]$Method,
        [Parameter(Mandatory = $true)] [string]$Uri,
        [object]$Body,
        [hashtable]$Headers
    )

    $params = @{
        Method      = $Method
        Uri         = $Uri
        TimeoutSec  = 30
        ErrorAction = "Stop"
    }
    if ($Headers) {
        $params.Headers = $Headers
    }
    if ($null -ne $Body) {
        $json = $Body | ConvertTo-Json -Compress -Depth 12
        $params.Body = [System.Text.Encoding]::UTF8.GetBytes($json)
        $params.ContentType = "application/json; charset=utf-8"
    }
    return Invoke-RestMethod @params
}

function Get-ClipboardSecret {
    $value = (Get-Clipboard) -join "`n"
    if ([string]::IsNullOrWhiteSpace($value)) {
        throw "Clipboard is empty. Copy the complete platform password first."
    }
    return $value.Trim()
}

function Normalize-Items {
    param([object]$Value)
    if ($null -eq $Value) {
        return @()
    }
    if ($Value.PSObject.Properties.Name -contains "value") {
        return @($Value.value)
    }
    return @($Value)
}

function Resolve-PlatformUrl {
    param([string]$Base, [string]$Url)
    if ($Url -match '^https?://') {
        return $Url
    }
    $baseUri = [Uri]($Base.TrimEnd('/') + '/')
    return ([Uri]::new($baseUri, $Url.TrimStart('/'))).AbsoluteUri
}

function Safe-FileName {
    param([string]$Name)
    $invalid = [IO.Path]::GetInvalidFileNameChars()
    $chars = $Name.ToCharArray() | ForEach-Object { if ($invalid -contains $_) { '_' } else { $_ } }
    return (-join $chars)
}

function Find-MiniappProjects {
    param([string]$Root)
    if (-not (Test-Path -LiteralPath $Root)) {
        return @()
    }
    $markers = Get-ChildItem -LiteralPath $Root -Recurse -File -Include project.config.json,app.json,pages.json,manifest.json,package.json -ErrorAction SilentlyContinue
    $dirs = New-Object System.Collections.Generic.HashSet[string]
    foreach ($marker in $markers) {
        [void]$dirs.Add($marker.Directory.FullName)
    }
    return $dirs | Sort-Object
}

if ([string]::IsNullOrWhiteSpace($Username)) {
    $Username = -join ([char]0x7b2c, "12", [char]0x7ec4)
}

$normalizedBaseUrl = $BaseUrl.TrimEnd("/")
$outputPath = Resolve-Path -LiteralPath .
$documentDir = Join-Path $outputPath $OutputDir
$projectDir = Join-Path $outputPath $ProjectOutputDir
New-Item -ItemType Directory -Force -Path $documentDir | Out-Null
New-Item -ItemType Directory -Force -Path $projectDir | Out-Null

Write-Host "Platform: $normalizedBaseUrl"
Write-Host "Username: $Username"
Write-Host "Target group: $TesteeId, phase: $Phase"
Write-Host "Password source: clipboard (not printed, not saved)"

$password = Get-ClipboardSecret
try {
    $login = Invoke-JsonRequest -Method "POST" -Uri "$normalizedBaseUrl/api/auth/login" -Body @{ username = $Username; password = $password }
}
finally {
    $password = $null
    if ($ClearClipboardAfterRead) {
        try {
            Set-Clipboard -Value " "
        }
        catch {
            Write-Host "Clipboard clear failed: $($_.Exception.Message)"
        }
    }
}

if (-not $login.token) {
    throw "Login response did not include token."
}
$headers = @{ Authorization = "Bearer $($login.token)" }
Write-Host "Login: OK"

$slots = Normalize-Items (Invoke-JsonRequest -Method "GET" -Uri "$normalizedBaseUrl/api/testing-relations/slots?phase=$Phase")
$targetSlot = $slots | Where-Object { $_.group_id -eq $TesteeId } | Select-Object -First 1
if ($targetSlot) {
    Write-Host "Slot: official_count=$($targetSlot.official_count), slots_left=$($targetSlot.slots_left), full=$($targetSlot.full), coef=$($targetSlot.coef)"
}

$relations = Normalize-Items (Invoke-JsonRequest -Method "GET" -Uri "$normalizedBaseUrl/api/testing-relations/my" -Headers $headers)
$existing = $relations | Where-Object { $_.testee_id -eq $TesteeId -or $_.testee_group_id -eq $TesteeId -or $_.testee.id -eq $TesteeId } | Select-Object -First 1
if ($existing) {
    Write-Host "Relation: group $TesteeId is already in my testing targets."
}
elseif ($RegisterIfMissing) {
    Write-Host "Relation: not found, registering group $TesteeId..."
    $created = Invoke-JsonRequest -Method "POST" -Uri "$normalizedBaseUrl/api/testing-relations" -Headers $headers -Body @{ testee_id = $TesteeId; phase = $Phase }
    Write-Host "Relation: registered, id=$($created.id)"
}
else {
    Write-Host "Relation: group $TesteeId not found in my targets. Use -RegisterIfMissing if you want to register automatically."
}

$documents = Normalize-Items (Invoke-JsonRequest -Method "GET" -Uri "$normalizedBaseUrl/api/documents/group/$TesteeId" -Headers $headers)
if (-not $documents -or $documents.Count -eq 0) {
    Write-Host "Documents: no group $TesteeId documents returned."
}
else {
    Write-Host "Documents: $($documents.Count) file(s)"
}

$downloaded = @()
foreach ($doc in $documents) {
    $rawFileName = $doc.filename
    if ([string]::IsNullOrWhiteSpace($rawFileName)) {
        $rawFileName = "group-$TesteeId-doc-$($doc.id)"
    }
    $fileName = Safe-FileName $rawFileName
    $targetPath = Join-Path $documentDir $fileName
    $downloadUrl = Resolve-PlatformUrl -Base $normalizedBaseUrl -Url $doc.url
    Invoke-WebRequest -Uri $downloadUrl -Headers $headers -OutFile $targetPath -TimeoutSec 60
    $downloaded += $targetPath
    Write-Host "Downloaded: $targetPath"
}

$extractRoot = Join-Path $projectDir "extracted"
New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null
foreach ($file in $downloaded) {
    if ([IO.Path]::GetExtension($file).ToLowerInvariant() -eq ".zip") {
        $dest = Join-Path $extractRoot ([IO.Path]::GetFileNameWithoutExtension($file))
        if (Test-Path -LiteralPath $dest) {
            Remove-Item -LiteralPath $dest -Recurse -Force
        }
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        Expand-Archive -LiteralPath $file -DestinationPath $dest -Force
        Write-Host "Extracted: $dest"
    }
}

$projects = @(Find-MiniappProjects -Root $projectDir)
$summaryPath = Join-Path $projectDir "SETUP_SUMMARY.md"
$summary = @()
$summary += "# Group 14 local miniapp setup summary"
$summary += ""
$summary += "- Platform: $normalizedBaseUrl"
$summary += "- Tester: $Username"
$summary += "- Testee: group $TesteeId"
$summary += "- Documents: $documentDir"
$summary += "- Extracted root: $extractRoot"
$summary += "- Password: not saved"
$summary += ""
$summary += "## Downloaded files"
if ($downloaded.Count -eq 0) {
    $summary += "- No files downloaded"
}
else {
    foreach ($file in $downloaded) {
        $summary += "- $file"
    }
}
$summary += ""
$summary += "## Candidate project directories"
if ($projects.Count -eq 0) {
    $summary += "- No project.config.json, app.json, pages.json, manifest.json, or package.json was found. If the platform only provides a PDF, ask group 14 for the miniapp source package."
}
else {
    foreach ($project in $projects) {
        $summary += "- $project"
    }
}
$summary | Set-Content -LiteralPath $summaryPath -Encoding UTF8
Write-Host "Summary: $summaryPath"

if ($projects.Count -gt 0) {
    Write-Host "Candidate project directories:"
    $projects | ForEach-Object { Write-Host "- $_" }
}
else {
    Write-Host "No local miniapp project markers found after download/extract."
}
