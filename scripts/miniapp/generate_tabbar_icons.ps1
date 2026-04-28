param(
    [string]$OutputDir = (Join-Path $PSScriptRoot '..\..\miniapp\src\static')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

try {
    Add-Type -AssemblyName System.Drawing.Common
} catch {
    Add-Type -AssemblyName System.Drawing
}

$resolvedOutputDir = [System.IO.Path]::GetFullPath($OutputDir)
New-Item -ItemType Directory -Path $resolvedOutputDir -Force | Out-Null

function New-StrokePen {
    param(
        [System.Drawing.Color]$Color,
        [single]$Width
    )

    $pen = [System.Drawing.Pen]::new($Color, $Width)
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
    return $pen
}

function Save-Icon {
    param(
        [string]$FileName,
        [System.Drawing.Color]$Color,
        [scriptblock]$Paint
    )

    $size = 96
    $bitmap = [System.Drawing.Bitmap]::new($size, $size)
    try {
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
            $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
            $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
            $graphics.Clear([System.Drawing.Color]::Transparent)

            & $Paint $graphics $Color

            $outputPath = Join-Path $resolvedOutputDir $FileName
            $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
            Write-Output $outputPath
        } finally {
            $graphics.Dispose()
        }
    } finally {
        $bitmap.Dispose()
    }
}

function Draw-HomeIcon {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Color]$Color
    )

    $pen = New-StrokePen -Color $Color -Width 6
    try {
        $roof = [System.Drawing.Point[]]@(
            [System.Drawing.Point]::new(20, 42),
            [System.Drawing.Point]::new(48, 18),
            [System.Drawing.Point]::new(76, 42)
        )
        $Graphics.DrawLines($pen, $roof)
        $Graphics.DrawRectangle($pen, 28, 40, 40, 32)
        $Graphics.DrawLine($pen, 48, 72, 48, 54)
    } finally {
        $pen.Dispose()
    }
}

function Draw-BellIcon {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Color]$Color
    )

    $pen = New-StrokePen -Color $Color -Width 6
    $brush = [System.Drawing.SolidBrush]::new($Color)
    try {
        $Graphics.DrawArc($pen, 26, 18, 44, 34, 180, 180)
        $Graphics.DrawLine($pen, 26, 35, 22, 58)
        $Graphics.DrawLine($pen, 70, 35, 74, 58)
        $Graphics.DrawArc($pen, 22, 50, 52, 12, 0, 180)
        $Graphics.DrawLine($pen, 48, 18, 48, 12)
        $Graphics.FillEllipse($brush, 44, 62, 8, 8)
    } finally {
        $pen.Dispose()
        $brush.Dispose()
    }
}

function Draw-ProfileIcon {
    param(
        [System.Drawing.Graphics]$Graphics,
        [System.Drawing.Color]$Color
    )

    $pen = New-StrokePen -Color $Color -Width 6
    try {
        $Graphics.DrawEllipse($pen, 30, 16, 36, 36)
        $Graphics.DrawArc($pen, 20, 44, 56, 28, 205, 130)
    } finally {
        $pen.Dispose()
    }
}

$inactiveColor = [System.Drawing.ColorTranslator]::FromHtml('#999999')
$activeColor = [System.Drawing.ColorTranslator]::FromHtml('#7f1722')

$iconSpecs = @(
    @{ FileName = 'tab-home.png'; Color = $inactiveColor; Paint = ${function:Draw-HomeIcon} },
    @{ FileName = 'tab-home-active.png'; Color = $activeColor; Paint = ${function:Draw-HomeIcon} },
    @{ FileName = 'tab-notice.png'; Color = $inactiveColor; Paint = ${function:Draw-BellIcon} },
    @{ FileName = 'tab-notice-active.png'; Color = $activeColor; Paint = ${function:Draw-BellIcon} },
    @{ FileName = 'tab-profile.png'; Color = $inactiveColor; Paint = ${function:Draw-ProfileIcon} },
    @{ FileName = 'tab-profile-active.png'; Color = $activeColor; Paint = ${function:Draw-ProfileIcon} }
)

foreach ($icon in $iconSpecs) {
    Save-Icon -FileName $icon.FileName -Color $icon.Color -Paint $icon.Paint | Out-Null
}

Write-Output "Generated tab bar icons in $resolvedOutputDir"
