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

function Get-IconFontFamily {
    $preferred = @('Microsoft YaHei UI', 'Microsoft YaHei', 'SimHei', 'Arial')
    $families = [System.Drawing.FontFamily]::Families | ForEach-Object { $_.Name }
    foreach ($name in $preferred) {
        if ($families -contains $name) {
            return $name
        }
    }
    return [System.Drawing.FontFamily]::GenericSansSerif.Name
}

function New-RoundedRectanglePath {
    param(
        [single]$X,
        [single]$Y,
        [single]$Width,
        [single]$Height,
        [single]$Radius
    )

    $diameter = $Radius * 2
    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    $path.AddArc($X, $Y, $diameter, $diameter, 180, 90)
    $path.AddArc($X + $Width - $diameter, $Y, $diameter, $diameter, 270, 90)
    $path.AddArc($X + $Width - $diameter, $Y + $Height - $diameter, $diameter, $diameter, 0, 90)
    $path.AddArc($X, $Y + $Height - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()
    return $path
}

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

function Draw-AppIcon {
    param(
        [System.Drawing.Graphics]$Graphics,
        [int]$Size
    )

    $Graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $Graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $Graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
    $Graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $Graphics.Clear([System.Drawing.ColorTranslator]::FromHtml('#b70f24'))

    $scale = [single]($Size / 1024.0)
    $bgRect = [System.Drawing.RectangleF]::new(0, 0, $Size, $Size)
    $bgPath = New-RoundedRectanglePath -X 0 -Y 0 -Width $Size -Height $Size -Radius ([single](184 * $scale))
    $bgBrush = [System.Drawing.Drawing2D.LinearGradientBrush]::new(
        $bgRect,
        [System.Drawing.ColorTranslator]::FromHtml('#cf2038'),
        [System.Drawing.ColorTranslator]::FromHtml('#7f1120'),
        [System.Drawing.Drawing2D.LinearGradientMode]::ForwardDiagonal
    )
    try {
        $Graphics.FillPath($bgBrush, $bgPath)
    } finally {
        $bgBrush.Dispose()
        $bgPath.Dispose()
    }

    $glowBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(46, 255, 238, 225))
    try {
        $Graphics.FillEllipse($glowBrush, -120 * $scale, -90 * $scale, 620 * $scale, 430 * $scale)
    } finally {
        $glowBrush.Dispose()
    }

    $innerPath = New-RoundedRectanglePath -X ([single](64 * $scale)) -Y ([single](64 * $scale)) -Width ([single](896 * $scale)) -Height ([single](896 * $scale)) -Radius ([single](148 * $scale))
    $borderPen = [System.Drawing.Pen]::new([System.Drawing.Color]::FromArgb(74, 255, 255, 255), [single](10 * $scale))
    try {
        $Graphics.DrawPath($borderPen, $innerPath)
    } finally {
        $borderPen.Dispose()
        $innerPath.Dispose()
    }

    $markShadowBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(58, 60, 0, 12))
    $markBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(250, 255, 255, 255))
    $font = [System.Drawing.Font]::new((Get-IconFontFamily), [single](500 * $scale), [System.Drawing.FontStyle]::Bold, [System.Drawing.GraphicsUnit]::Pixel)
    $format = [System.Drawing.StringFormat]::new()
    $format.Alignment = [System.Drawing.StringAlignment]::Center
    $format.LineAlignment = [System.Drawing.StringAlignment]::Center
    try {
        $textRect = [System.Drawing.RectangleF]::new([single](0), [single](58 * $scale), [single]$Size, [single](646 * $scale))
        $shadowRect = [System.Drawing.RectangleF]::new([single](0), [single](70 * $scale), [single]$Size, [single](646 * $scale))
        $Graphics.DrawString('信', $font, $markShadowBrush, $shadowRect, $format)
        $Graphics.DrawString('信', $font, $markBrush, $textRect, $format)
    } finally {
        $font.Dispose()
        $format.Dispose()
        $markBrush.Dispose()
        $markShadowBrush.Dispose()
    }

    $bookPen = New-StrokePen -Color ([System.Drawing.Color]::FromArgb(235, 255, 255, 255)) -Width ([single](38 * $scale))
    $thinPen = New-StrokePen -Color ([System.Drawing.Color]::FromArgb(170, 255, 220, 160)) -Width ([single](18 * $scale))
    $dotBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(245, 255, 219, 126))
    $whiteDotBrush = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(245, 255, 255, 255))
    try {
        $Graphics.DrawBezier($bookPen, 214 * $scale, 762 * $scale, 326 * $scale, 700 * $scale, 430 * $scale, 704 * $scale, 512 * $scale, 760 * $scale)
        $Graphics.DrawBezier($bookPen, 512 * $scale, 760 * $scale, 594 * $scale, 704 * $scale, 698 * $scale, 700 * $scale, 810 * $scale, 762 * $scale)
        $Graphics.DrawLine($thinPen, 304 * $scale, 836 * $scale, 720 * $scale, 836 * $scale)
        $Graphics.FillEllipse($whiteDotBrush, 284 * $scale, 816 * $scale, 40 * $scale, 40 * $scale)
        $Graphics.FillEllipse($dotBrush, 492 * $scale, 814 * $scale, 44 * $scale, 44 * $scale)
        $Graphics.FillEllipse($whiteDotBrush, 700 * $scale, 816 * $scale, 40 * $scale, 40 * $scale)
    } finally {
        $bookPen.Dispose()
        $thinPen.Dispose()
        $dotBrush.Dispose()
        $whiteDotBrush.Dispose()
    }
}

function Save-AppIcon {
    param(
        [int]$Size,
        [string]$FileName
    )

    $bitmap = [System.Drawing.Bitmap]::new($Size, $Size)
    try {
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        try {
            Draw-AppIcon -Graphics $graphics -Size $Size
        } finally {
            $graphics.Dispose()
        }

        $outputPath = Join-Path $resolvedOutputDir $FileName
        $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        Write-Output $outputPath
    } finally {
        $bitmap.Dispose()
    }
}

$iconSpecs = @(
    @{ Size = 1024; FileName = 'app-icon.png' },
    @{ Size = 512; FileName = 'app-icon-512.png' },
    @{ Size = 144; FileName = 'app-icon-144.png' }
)

foreach ($icon in $iconSpecs) {
    Save-AppIcon -Size $icon.Size -FileName $icon.FileName | Out-Null
}

Write-Output "Generated miniapp app icons in $resolvedOutputDir"
