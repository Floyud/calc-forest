$ErrorActionPreference = "Stop"

$sourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$wdFormatPDF = 17
$failures = @()

function Close-DocumentIfOpen {
    param([object]$Document)
    if ($null -ne $Document) {
        try {
            $Document.Close([ref]$false)
        } catch {
        }
    }
}

try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0

    Get-ChildItem -Path $sourceDir -Filter *.docx | Sort-Object Name | ForEach-Object {
        $doc = $null
        $inputPath = $_.FullName
        $outputPath = [System.IO.Path]::ChangeExtension($inputPath, ".pdf")

        try {
            if (Test-Path $outputPath) {
                Remove-Item -LiteralPath $outputPath -Force
            }

            $doc = $word.Documents.Open($inputPath, $false, $true)
            $doc.SaveAs([ref]$outputPath, [ref]$wdFormatPDF)
            Write-Output ("OK`t" + $_.Name)
        } catch {
            $failures += [PSCustomObject]@{
                file = $_.Name
                error = $_.Exception.Message
            }
            Write-Output ("FAIL`t" + $_.Name + "`t" + $_.Exception.Message)
        } finally {
            Close-DocumentIfOpen -Document $doc
        }
    }
} finally {
    if ($null -ne $word) {
        try {
            $word.Quit()
        } catch {
        }
    }

    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
}

if ($failures.Count -gt 0) {
    $failures | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $sourceDir "export_teacher_feedback_pdf_failures.json") -Encoding UTF8
    exit 1
}

Remove-Item -LiteralPath (Join-Path $sourceDir "export_teacher_feedback_pdf_failures.json") -ErrorAction SilentlyContinue
