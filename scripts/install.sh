#!/usr/bin/env sh
set -eu

REPO="shadohead/3ds-ftpd-transfer"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
BIN_NAME="3ds-ftpd-transfer"

detect_asset() {
  os="$(uname -s)"
  arch="$(uname -m)"

  case "$os:$arch" in
    Darwin:arm64) echo "3ds-ftpd-transfer-macos-arm64.tar.gz" ;;
    Darwin:x86_64) echo "3ds-ftpd-transfer-macos-x64.tar.gz" ;;
    Linux:x86_64) echo "3ds-ftpd-transfer-linux-x64.tar.gz" ;;
    *)
      echo "Unsupported platform: $os $arch" >&2
      exit 1
      ;;
  esac
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need_cmd curl
need_cmd tar

ASSET="$(detect_asset)"
URL="https://github.com/$REPO/releases/latest/download/$ASSET"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT INT TERM

echo "Downloading $ASSET..."
curl -fL "$URL" -o "$TMP_DIR/$ASSET"

echo "Extracting..."
tar -xzf "$TMP_DIR/$ASSET" -C "$TMP_DIR"

mkdir -p "$INSTALL_DIR"
cp "$TMP_DIR/$BIN_NAME" "$INSTALL_DIR/$BIN_NAME"
chmod +x "$INSTALL_DIR/$BIN_NAME"

if command -v xattr >/dev/null 2>&1; then
  xattr -d com.apple.quarantine "$INSTALL_DIR/$BIN_NAME" >/dev/null 2>&1 || true
fi

echo
echo "Installed:"
echo "  $INSTALL_DIR/$BIN_NAME"
echo
if command -v "$BIN_NAME" >/dev/null 2>&1; then
  echo "Run it with:"
  echo "  $BIN_NAME"
else
  echo "Run it with:"
  echo "  $INSTALL_DIR/$BIN_NAME"
  echo
  echo "Optional: add this to your shell profile so '$BIN_NAME' works everywhere:"
  echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
echo
echo "Uninstall with:"
echo "  curl -fsSL https://raw.githubusercontent.com/$REPO/main/scripts/uninstall.sh | sh"
