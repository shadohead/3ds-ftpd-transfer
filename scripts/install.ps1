$ErrorActionPreference = "Stop"

$Repo = "shadohead/3ds-ftpd-transfer"
$InstallDir = if ($env:INSTALL_DIR) { $env:INSTALL_DIR } else { Join-Path $env:LOCALAPPDATA "Programs\3ds-ftpd-transfer" }
$ExeName = "3ds-ftpd-transfer.exe"
$Asset = "3ds-ftpd-transfer-windows-x64.exe.zip"
$Url = "https://github.com/$Repo/releases/latest/download/$Asset"
$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("3ds-ftpd-transfer-" + [System.Guid]::NewGuid())

New-Item -ItemType Directory -Path $TempDir | Out-Null

try {
    $ZipPath = Join-Path $TempDir $Asset
    Write-Host "Downloading $Asset..."
    Invoke-WebRequest -Uri $Url -OutFile $ZipPath

    Write-Host "Extracting..."
    Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force

    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Copy-Item -Path (Join-Path $TempDir $ExeName) -Destination (Join-Path $InstallDir $ExeName) -Force

    Write-Host ""
    Write-Host "Installed:"
    Write-Host "  $(Join-Path $InstallDir $ExeName)"
    Write-Host ""
    Write-Host "Run it with:"
    Write-Host "  & `"$InstallDir\$ExeName`""
    Write-Host ""
    Write-Host "Uninstall with:"
    Write-Host "  irm https://raw.githubusercontent.com/$Repo/main/scripts/uninstall.ps1 | iex"
}
finally {
    Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
