# 3DS ftpd Transfer

A small browser-based helper for sending files to a Nintendo 3DS running
[`ftpd`](https://github.com/mtheall/ftpd).

It starts a local web UI, opens it in your browser, and transfers either a local
file or a direct legal/homebrew download URL to a folder on the 3DS SD card.

This tool does not include ROM search, archive scraping, or copyrighted-content
download integration.

## Documentation

The full setup and usage guide is published here:

https://shadohead.github.io/3ds-ftpd-transfer/

It covers installing the app, sending files, NDS cheat databases, NDS forwarder
setup, SD card preparation notes, and what a hosted website can and cannot do.

## Easy Install

This installs only the `3ds-ftpd-transfer` executable into a user-owned folder.
No Python, Homebrew, admin password, or system package manager is required.

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/shadohead/3ds-ftpd-transfer/main/scripts/install.sh | sh
```

Uninstall:

```bash
curl -fsSL https://raw.githubusercontent.com/shadohead/3ds-ftpd-transfer/main/scripts/uninstall.sh | sh
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/shadohead/3ds-ftpd-transfer/main/scripts/install.ps1 | iex
```

Uninstall:

```powershell
irm https://raw.githubusercontent.com/shadohead/3ds-ftpd-transfer/main/scripts/uninstall.ps1 | iex
```

## Direct Download

Use the latest GitHub Release for your operating system:

- macOS: `3ds-ftpd-transfer-macos-*`
- Windows: `3ds-ftpd-transfer-windows-x64.exe.zip`
- Linux: `3ds-ftpd-transfer-linux-*`

The release binaries are built with PyInstaller, so Python is not required.

## Quick Start

1. Install/open `ftpd` on your 3DS.
2. Note the IP address and port shown on the 3DS screen.
3. Run `3ds-ftpd-transfer`.
4. Your browser opens the transfer page.
5. Enter the 3DS IP address and port.
6. Choose a destination folder, such as:
   - `/3ds/inbox`
   - `/roms/nds`
   - `/cias`
7. Choose a local file or paste a direct legal/homebrew URL.
8. Click **Send to 3DS**.
9. Click **Quit** when finished.

## NDS Cheat Database Helper

The app can install a TWiLight Menu++ cheat database directly to:

```text
/_nds/TWiLightMenu/extras/usrcheat.dat
```

Open `ftpd` on the 3DS, enter the same IP and port, then use the
**NDS cheats for TWiLight Menu++** panel. You can choose a local
`usrcheat.dat`, `.zip`, or `.7z` file, or paste a direct download URL to one of
those files.

The source page for DeadSkullzJr's database is:

https://www.gamebrew.org/wiki/DeadSkullzJr_NDS_Cheat_Databases

GameBrew lists TWiLight Menu++ as using `usrcheat.dat` at
`SD:/_nds/TWiLightMenu/extras/usrcheat.dat`.

## macOS First Run

The macOS release binaries are not Apple-notarized yet. On first run, macOS may
show:

> Apple could not verify "3ds-ftpd-transfer" is free of malware that may harm
> your Mac or compromise your privacy.

To open it anyway:

1. Right-click or Control-click `3ds-ftpd-transfer`.
2. Choose **Open**.
3. Click **Open** again in the warning dialog.

If macOS still blocks it, remove the download quarantine flag after extracting
the archive:

```bash
xattr -dr com.apple.quarantine ./3ds-ftpd-transfer
chmod +x ./3ds-ftpd-transfer
./3ds-ftpd-transfer
```

The long-term fix is to sign and notarize the macOS builds with an Apple
Developer ID certificate.

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e . -r requirements-dev.txt
python -m pytest
python -m ftpd_transfer
```

## Build a Local Binary

```bash
python -m pip install -r requirements-dev.txt
pyinstaller --clean --onefile --name 3ds-ftpd-transfer src/ftpd_transfer/__main__.py
```

The binary will be in `dist/`.

## Legal Use

Use this for homebrew, patches, saves, themes, and backups you are legally
allowed to copy. It is not a downloader for copyrighted commercial ROMs.
