param(
    [string]$BaseUrl = "http://183.174.61.212:8001",
    [string]$Username = "",
    [int]$TesteeId = 16,
    [int]$Phase = 1,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

function ConvertTo-JsonBytes {
    param([Parameter(Mandatory = $true)] [object]$Value)
    $json = $Value | ConvertTo-Json -Compress -Depth 8
    return [System.Text.Encoding]::UTF8.GetBytes($json)
}

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
        $params.Body = ConvertTo-JsonBytes -Value $Body
        $params.ContentType = "application/json; charset=utf-8"
    }
    return Invoke-RestMethod @params
}

function Get-PasswordPlainText {
    $secure = Read-Host "Enter platform password for the configured group (input is hidden)" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    }
    finally {
        if ($ptr -ne [IntPtr]::Zero) {
            [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        }
    }
}

if ([string]::IsNullOrWhiteSpace($Username)) {
    $Username = -join ([char]0x7b2c, "12", [char]0x7ec4)
}

$normalizedBaseUrl = $BaseUrl.TrimEnd("/")
Write-Host "BaseUrl: $normalizedBaseUrl"
Write-Host "Username: $Username"
Write-Host "Target: group $TesteeId, phase $Phase"

$slots = Invoke-JsonRequest -Method "GET" -Uri "$normalizedBaseUrl/api/testing-relations/slots?phase=$Phase"
$targetSlot = $slots | Where-Object { $_.group_id -eq $TesteeId } | Select-Object -First 1
if (-not $targetSlot) {
    throw "Group $TesteeId was not found in slot list."
}

Write-Host "Current slots: official_count=$($targetSlot.official_count), slots_left=$($targetSlot.slots_left), full=$($targetSlot.full), coef=$($targetSlot.coef)"
if ($targetSlot.full -or [int]$targetSlot.slots_left -le 0) {
    throw "Group $TesteeId has no official testing slots left. Choose another candidate."
}

if ($DryRun) {
    Write-Host "DryRun: checked slots only. Login and official registration were not executed."
    exit 0
}

$password = Get-PasswordPlainText
try {
    $login = Invoke-JsonRequest -Method "POST" -Uri "$normalizedBaseUrl/api/auth/login" -Body @{ username = $Username; password = $password }
}
finally {
    $password = $null
}

if (-not $login.token) {
    throw "Login response did not include a token. Cannot register target."
}

$headers = @{ Authorization = "Bearer $($login.token)" }
$relation = Invoke-JsonRequest -Method "POST" -Uri "$normalizedBaseUrl/api/testing-relations" -Headers $headers -Body @{ testee_id = $TesteeId; phase = $Phase }
Write-Host "Registration request submitted. Platform response:"
$relation | ConvertTo-Json -Depth 8

Write-Host "`nMy testing relations:"
$myRelations = Invoke-JsonRequest -Method "GET" -Uri "$normalizedBaseUrl/api/testing-relations/my" -Headers $headers
$myRelations | ConvertTo-Json -Depth 8

try {
    $documents = Invoke-JsonRequest -Method "GET" -Uri "$normalizedBaseUrl/api/documents/all" -Headers $headers
    $targetDocuments = $documents | Where-Object { $_.group_id -eq $TesteeId }
    if ($targetDocuments) {
        Write-Host "`nGroup $TesteeId documents:"
        $targetDocuments | ConvertTo-Json -Depth 8
    }
    else {
        Write-Host "`nNo group $TesteeId documents were returned by /api/documents/all. Check the platform page manually."
    }
}
catch {
    Write-Host "`nFailed to read document list. Check the platform page manually: $($_.Exception.Message)"
}
