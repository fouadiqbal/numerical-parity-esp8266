param(
    [string]$InputFile,
    [string]$OutputFile
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot

if ([string]::IsNullOrWhiteSpace($InputFile)) {
    $captureDirectory = Join-Path $repositoryRoot "data\esp8266"
    $latestCapture = Get-ChildItem -LiteralPath $captureDirectory -Filter "*.jsonl" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latestCapture) {
        throw "No ESP8266 JSONL capture was found in $captureDirectory"
    }
    $InputFile = $latestCapture.FullName
}

$resolvedInput = (Resolve-Path -LiteralPath $InputFile).Path
if ([string]::IsNullOrWhiteSpace($OutputFile)) {
    $OutputFile = [System.IO.Path]::ChangeExtension($resolvedInput, ".csv")
}

$records = Get-Content -LiteralPath $resolvedInput |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_) } |
    ForEach-Object { $_ | ConvertFrom-Json }

$records |
    Select-Object captured_at_utc, uptime_ms, raw_adc, load_kw, anomaly,
        wifi_rssi_dbm, http_code, thingspeak_entry_id |
    Export-Csv -LiteralPath $OutputFile -NoTypeInformation -Encoding utf8

Write-Host "Converted $($records.Count) records"
Write-Host "CSV: $OutputFile"
