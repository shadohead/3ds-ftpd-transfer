$ErrorActionPreference = "Stop"

$InstallDir = if ($env:INSTALL_DIR) { $env:INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA "Programs\3ds-ftpd-transfer" }
$Target = Join-Path $InstallDir "3ds-ftpd-transfer.exe"

if (Test-Path $Target) {
    Remove-Item -Path $Target -Force
    Write-Host "Removed $Target"
}
else {
    Write-Host "Nothing to remove at $Target"
}

if ((Test-Path $InstallDir) -and -not (Get-ChildItem $InstallDir -Force -ErrorAction SilentlyContinue)) {
    Remove-Item -Path $InstallDir -Force
    Write-Host "Removed empty folder $InstallDir"
}
