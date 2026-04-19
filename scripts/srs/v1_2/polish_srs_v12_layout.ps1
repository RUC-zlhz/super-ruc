$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$docItem = Get-ChildItem (Join-Path $repoRoot 'output\doc\*v1.2.docx') | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $docItem) {
    throw 'Cannot find v1.2 DOCX under output\doc.'
}
$docPath = $docItem.FullName
$pdfPath = [System.IO.Path]::ChangeExtension($docPath, '.pdf')
$previewPath = Join-Path $repoRoot 'tmp\docs\final_srs_preview.pdf'

$wdAlignParagraphLeft = 0
$wdAlignParagraphCenter = 1
$wdRowHeightExactly = 2
$wdLineSpaceSingle = 0

function Set-CellParagraphTight {
    param($cellRange, [double]$fontSize = 10.0)
    foreach ($paragraph in $cellRange.Paragraphs) {
        $paragraph.Range.Font.Size = $fontSize
        $paragraph.Range.ParagraphFormat.SpaceBefore = 0
        $paragraph.Range.ParagraphFormat.SpaceAfter = 0
        $paragraph.Range.ParagraphFormat.LineSpacingRule = $wdLineSpaceSingle
    }
}

function Find-ParagraphByText {
    param($doc, [string]$target)
    for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
        $paragraph = $doc.Paragraphs.Item($i)
        if ($paragraph.Range.Text.Trim() -eq $target) {
            return $paragraph
        }
    }
    return $null
}

function New-LiteralFromCodePoints {
    param([int[]]$CodePoints)
    return (-join ($CodePoints | ForEach-Object { [char]$_ }))
}

$styleHeading1Zh = New-LiteralFromCodePoints @(26631, 39064, 32, 49)
$styleHeading3Zh = New-LiteralFromCodePoints @(26631, 39064, 32, 51)
$sectionSoftwarePrototype = New-LiteralFromCodePoints @(53, 46, 32, 36719, 20214, 21407, 22411)
$leadInSystemContext = New-LiteralFromCodePoints @(31995, 32479, 19982, 22806, 37096, 29615, 22659, 30340, 20851, 31995, 22914, 22270, 25152, 31034, 65306)
$leadInSequence = New-LiteralFromCodePoints @(20851, 38190, 21160, 24577, 20132, 20114, 37319, 29992, 35831, 20551, 30003, 35831, 19982, 21518, 21488, 23457, 26680, 20316, 20026, 20856, 22411, 26102, 24207, 36827, 34892, 35828, 26126, 12290)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$document = $word.Documents.Open($docPath)

# Cover: align title information on a single axis and strengthen hierarchy.
$coverParagraphs = @{
    1  = @{ Size = 11; Bold = $false; Align = $wdAlignParagraphCenter; SpaceAfter = 18 }
    12 = @{ Size = 26; Bold = $true; Align = $wdAlignParagraphCenter; SpaceAfter = 6 }
    13 = @{ Size = 22; Bold = $true; Align = $wdAlignParagraphCenter; SpaceAfter = 120 }
    32 = @{ Size = 12; Bold = $false; Align = $wdAlignParagraphCenter; SpaceBefore = 24 }
}
foreach ($idx in $coverParagraphs.Keys) {
    $paragraph = $document.Paragraphs.Item($idx)
    $cfg = $coverParagraphs[$idx]
    $paragraph.Range.ParagraphFormat.Alignment = $cfg.Align
    $paragraph.Range.Font.Size = $cfg.Size
    $paragraph.Range.Font.Bold = [int]($cfg.Bold)
    if ($cfg.ContainsKey('SpaceBefore')) { $paragraph.Range.ParagraphFormat.SpaceBefore = $cfg.SpaceBefore }
    if ($cfg.ContainsKey('SpaceAfter')) { $paragraph.Range.ParagraphFormat.SpaceAfter = $cfg.SpaceAfter }
}

# Change history page: keep a realistic number of blank rows and tighten the table.
$historyTable = $document.Tables.Item(1)
while ($historyTable.Rows.Count -gt 8) {
    $historyTable.Rows.Item($historyTable.Rows.Count).Delete()
}
$historyTable.Rows.Item(1).HeadingFormat = -1
$historyTable.Columns.Item(1).Width = 28
$historyTable.Columns.Item(2).Width = 66
$historyTable.Columns.Item(3).Width = 70
$historyTable.Columns.Item(4).Width = 300
$historyTable.Columns.Item(5).Width = 64
for ($r = 1; $r -le $historyTable.Rows.Count; $r++) {
    $row = $historyTable.Rows.Item($r)
    $row.HeightRule = $wdRowHeightExactly
    $row.Height = 18
    $row.AllowBreakAcrossPages = 0
    if ($r -eq 1) {
        $row.Range.Font.Bold = 1
    }
}
Set-CellParagraphTight $historyTable.Range 10.0

# TOC hierarchy: stronger first-level entries and cleaner spacing.
for ($i = 1; $i -le $document.Paragraphs.Count; $i++) {
        $paragraph = $document.Paragraphs.Item($i)
        $styleName = $paragraph.Style.NameLocal
        if ($styleName -eq 'toc 1') {
            $paragraph.Range.Font.Bold = 1
            $paragraph.Range.ParagraphFormat.SpaceBefore = 4
            $paragraph.Range.ParagraphFormat.SpaceAfter = 2
        }
        elseif ($styleName -eq 'toc 3') {
            $paragraph.Range.Font.Bold = 0
            $paragraph.Range.ParagraphFormat.LeftIndent = 12
            $paragraph.Range.ParagraphFormat.SpaceBefore = 0
            $paragraph.Range.ParagraphFormat.SpaceAfter = 0
        }
}

# Global heading rules.
for ($i = 1; $i -le $document.Paragraphs.Count; $i++) {
    $paragraph = $document.Paragraphs.Item($i)
    $text = $paragraph.Range.Text.Trim()
    $styleName = $paragraph.Style.NameLocal

    if ($styleName -eq $styleHeading1Zh -or $styleName -eq 'Heading 1') {
        $paragraph.Range.ParagraphFormat.KeepWithNext = -1
        $paragraph.Range.ParagraphFormat.SpaceBefore = 6
        $paragraph.Range.ParagraphFormat.SpaceAfter = 4
    }
    elseif ($styleName -eq $styleHeading3Zh -or $styleName -eq 'Heading 3') {
        $paragraph.Range.ParagraphFormat.KeepWithNext = -1
        $paragraph.Range.ParagraphFormat.SpaceBefore = 8
        $paragraph.Range.ParagraphFormat.SpaceAfter = 3
    }

    if ($text -eq $sectionSoftwarePrototype) {
        $paragraph.Range.ParagraphFormat.PageBreakBefore = -1
    }

    if ($text -like '- *') {
        $paragraph.Range.ParagraphFormat.KeepTogether = -1
        $paragraph.Range.ParagraphFormat.SpaceAfter = 1
    }
}

# Keep figure lead-ins attached to following images/captions.
foreach ($text in @(
    $leadInSystemContext,
    $leadInSequence
)) {
    $paragraph = Find-ParagraphByText $document $text
    if ($paragraph -ne $null) {
        $paragraph.Range.ParagraphFormat.KeepWithNext = -1
    }
}

# Cross-page tables: repeat header row, avoid row splitting, and tighten dense tables.
$tightTables = @(2, 6, 7, 8, 9, 10, 11, 12, 17, 18, 19, 20)
for ($t = 2; $t -le $document.Tables.Count; $t++) {
    $table = $document.Tables.Item($t)
    $table.Rows.Item(1).HeadingFormat = -1
    foreach ($row in $table.Rows) {
        $row.AllowBreakAcrossPages = 0
    }
    $fontSize = 10.0
    if ($tightTables -contains $t) {
        $fontSize = 9.5
    }
    Set-CellParagraphTight $table.Range $fontSize
}

# Slightly rebalance a few dense tables.
$document.Tables.Item(6).Columns.Item(1).Width = 48
$document.Tables.Item(6).Columns.Item(2).Width = 92
$document.Tables.Item(6).Columns.Item(3).Width = 80
$document.Tables.Item(6).Columns.Item(4).Width = 320

$document.Tables.Item(17).Columns.Item(1).Width = 75
$document.Tables.Item(17).Columns.Item(2).Width = 330
$document.Tables.Item(17).Columns.Item(3).Width = 120

$document.Tables.Item(19).Columns.Item(1).Width = 90
$document.Tables.Item(19).Columns.Item(2).Width = 335
$document.Tables.Item(19).Columns.Item(3).Width = 100

$document.Tables.Item(20).Columns.Item(1).Width = 50
$document.Tables.Item(20).Columns.Item(2).Width = 260
$document.Tables.Item(20).Columns.Item(3).Width = 215

$document.Repaginate()
$document.Fields.Update() | Out-Null
foreach ($toc in $document.TablesOfContents) { $toc.Update() }
$document.Save()
$document.ExportAsFixedFormat($pdfPath, 17)
$document.ExportAsFixedFormat($previewPath, 17)
$pages = $document.ComputeStatistics(2)
$document.Close()
$word.Quit()

Write-Output "DOCX=$docPath"
Write-Output "PDF=$pdfPath"
Write-Output "PREVIEW=$previewPath"
Write-Output "PAGES=$pages"
