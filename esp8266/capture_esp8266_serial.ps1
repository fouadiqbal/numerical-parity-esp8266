param(
    [string]$Port = "COM11",
    [int]$BaudRate = 115200,
    [string]$OutputDirectory = "data/esp8266",
    [int]$DurationSeconds = 90
)

$ErrorActionPreference = "Stop"

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$outputRoot = Join-Path $repositoryRoot $OutputDirectory
New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputFile = Join-Path $outputRoot "esp8266_serial_$timestamp.jsonl"
$serial = [System.IO.Ports.SerialPort]::new($Port, $BaudRate)
$serial.NewLine = "`n"
$serial.ReadTimeout = 2000

try {
    $serial.Open()
    Write-Host "Capturing $Port at $BaudRate baud"
    Write-Host "Output: $outputFile"
    if ($DurationSeconds -gt 0) {
        Write-Host "Capture duration: $DurationSeconds seconds"
    }
    else {
        Write-Host "Press Ctrl+C to stop."
    }

    $captureStarted = Get-Date

    while ($DurationSeconds -le 0 -or ((Get-Date) - $captureStarted).TotalSeconds -lt $DurationSeconds) {
        try {
            $line = $serial.ReadLine().Trim()
            if ([string]::IsNullOrWhiteSpace($line)) {
                continue
            }

            try {
                $record = $line | ConvertFrom-Json -ErrorAction Stop
                $record | Add-Member -NotePropertyName captured_at_utc -NotePropertyValue ([DateTime]::UtcNow.ToString("o"))
                $normalized = $record | ConvertTo-Json -Compress
                Add-Content -LiteralPath $outputFile -Value $normalized -Encoding utf8
                Write-Host $normalized
            }
            catch {
                Write-Host "[serial] $line"
            }
        }
        catch [System.TimeoutException] {
            continue
        }
    }

    Write-Host "Capture complete: $outputFile"
}
finally {
    if ($serial.IsOpen) {
        $serial.Close()
    }
    $serial.Dispose()
}
