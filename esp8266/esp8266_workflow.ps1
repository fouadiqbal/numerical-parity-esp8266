param(
    [ValidateSet("Build", "Upload", "Monitor")]
    [string]$Action = "Build",
    [string]$Port = "COM11",
    [string]$Fqbn = "esp8266:esp8266:nodemcuv2",
    [switch]$TestMode,
    [switch]$FullValidation,
    [string]$CredentialSourceSketch = (Join-Path $env:USERPROFILE "OneDrive\Documents\Arduino\smart_meter\smart_meter.ino"),
    [string]$ArduinoCli = (Join-Path $env:LOCALAPPDATA "Programs\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe")
)

$ErrorActionPreference = "Stop"

function Get-PrivateSketchValue {
    param(
        [string]$Source,
        [string]$VariableName
    )

    $pattern = 'const\s+char\s*\*\s*' + [regex]::Escape($VariableName) + '\s*=\s*"(?<value>(?:\\.|[^"])*)"\s*;'
    $match = [regex]::Match($Source, $pattern)
    if (-not $match.Success) {
        throw "Could not find $VariableName in the private credential source sketch."
    }
    return $match.Groups["value"].Value
}

if (-not (Test-Path -LiteralPath $ArduinoCli)) {
    throw "Arduino CLI was not found at: $ArduinoCli"
}

if ($Action -eq "Monitor") {
    & $ArduinoCli monitor --port $Port --fqbn $Fqbn --config baudrate=115200 --timestamp
    exit $LASTEXITCODE
}

if (-not (Test-Path -LiteralPath $CredentialSourceSketch)) {
    throw "Private credential source sketch was not found: $CredentialSourceSketch"
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$firmwareSource = $PSScriptRoot
$privateSource = Get-Content -Raw -LiteralPath $CredentialSourceSketch

$wifiSsid = Get-PrivateSketchValue -Source $privateSource -VariableName "WIFI_SSID"
$wifiPassword = Get-PrivateSketchValue -Source $privateSource -VariableName "WIFI_PASSWORD"
$thingSpeakKey = Get-PrivateSketchValue -Source $privateSource -VariableName "THINGSPEAK_KEY"

$temporaryRoot = Join-Path $env:TEMP ("smart-meter-esp8266-" + [guid]::NewGuid().ToString("N"))
$temporarySketch = Join-Path $temporaryRoot "esp8266_smart_meter"
New-Item -ItemType Directory -Path $temporarySketch -Force | Out-Null

try {
    $firmwareText = Get-Content -Raw -LiteralPath (Join-Path $firmwareSource "esp8266_smart_meter.ino")
    if ($TestMode) {
        $firmwareText = $firmwareText.Replace(
            "constexpr bool TEST_MODE = false;",
            "constexpr bool TEST_MODE = true;"
        )
        Write-Host "Diagnostic sequence enabled in temporary build."
    }
    if ($FullValidation) {
        $firmwareText = $firmwareText.Replace(
            "#define SMART_METER_ENABLE_FULL_VALIDATION 0",
            "#define SMART_METER_ENABLE_FULL_VALIDATION 1"
        )
        $validationHeader = Join-Path $firmwareSource "tinyml_validation_data.h"
        if (-not (Test-Path -LiteralPath $validationHeader)) {
            throw "Full validation header is missing. Run src/train_tinyml_edge_model.py first."
        }
        Copy-Item -LiteralPath $validationHeader -Destination $temporarySketch
        Write-Host "Full held-out validation enabled in temporary build."
    }
    [System.IO.File]::WriteAllText(
        (Join-Path $temporarySketch "esp8266_smart_meter.ino"),
        $firmwareText
    )
    Copy-Item -LiteralPath (Join-Path $firmwareSource "tinyml_model.h") -Destination $temporarySketch
    Copy-Item -LiteralPath (Join-Path $firmwareSource "tinyml_fixed_model.h") -Destination $temporarySketch
    Copy-Item -LiteralPath (Join-Path $firmwareSource "tinyml_fused_model.h") -Destination $temporarySketch

    $secretHeader = @"
#pragma once
#define SMART_METER_WIFI_SSID "$wifiSsid"
#define SMART_METER_WIFI_PASSWORD "$wifiPassword"
#define SMART_METER_THINGSPEAK_WRITE_KEY "$thingSpeakKey"
"@
    [System.IO.File]::WriteAllText((Join-Path $temporarySketch "secrets.h"), $secretHeader)

    if ($Action -eq "Upload") {
        Get-Process -Name "serial-monitor" -ErrorAction SilentlyContinue | Stop-Process -Force
        & $ArduinoCli compile --upload --port $Port --fqbn $Fqbn $temporarySketch
    }
    else {
        & $ArduinoCli compile --fqbn $Fqbn $temporarySketch
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Arduino $Action failed with exit code $LASTEXITCODE."
    }
}
finally {
    if (Test-Path -LiteralPath $temporaryRoot) {
        $resolvedTemporaryRoot = (Resolve-Path -LiteralPath $temporaryRoot).Path
        $resolvedSystemTemp = (Resolve-Path -LiteralPath $env:TEMP).Path
        if ($resolvedTemporaryRoot.StartsWith($resolvedSystemTemp, [System.StringComparison]::OrdinalIgnoreCase)) {
            Remove-Item -LiteralPath $resolvedTemporaryRoot -Recurse -Force
        }
    }
}
