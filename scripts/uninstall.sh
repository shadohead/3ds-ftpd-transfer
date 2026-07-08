#!/usr/bin/env sh
set -eu

INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"
BIN_NAME="3ds-ftpd-transfer"
TARGET="$INSTALL_DIR/$BIN_NAME"

if [ -f "$TARGET" ]; then
  rm -f "$TARGET"
  echo "Removed $TARGET"
else
  echo "Nothing to remove at $TARGET"
fi
