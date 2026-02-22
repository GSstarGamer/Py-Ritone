param(
  [string]$Version = "1.15.0",
  [string]$MinecraftModsDir = "$env:APPDATA\.minecraft\mods"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $MinecraftModsDir)) {
  New-Item -ItemType Directory -Path $MinecraftModsDir -Force | Out-Null
}

$target = Join-Path $MinecraftModsDir "baritone-api-fabric-$Version.jar"
$url = "https://github.com/cabaletta/baritone/releases/download/v$Version/baritone-api-fabric-$Version.jar"

Write-Host "Downloading $url"
Invoke-WebRequest -Uri $url -OutFile $target
Write-Host "Saved to $target"
