#!/usr/bin/env bash
# Hermes wrapper for Obsidian CLI against the Hermes Brain vault.
# Keeps direct file tools as default, but makes Obsidian-native graph/metadata
# commands easy and consistent.
set -euo pipefail

if ! command -v obsidian >/dev/null 2>&1; then
  echo "ERROR: obsidian CLI not found. Enable Obsidian Settings → General → Command line interface." >&2
  exit 127
fi

VAULT_PATH="${OBSIDIAN_VAULT_PATH:-$HOME/obsidian-vault/hermes-brain/}"
# Expand leading ~ because env files often store OBSIDIAN_VAULT_PATH=~/...
case "$VAULT_PATH" in
  \~) VAULT_PATH="$HOME" ;;
  \~/*) VAULT_PATH="$HOME/${VAULT_PATH:2}" ;;
esac
VAULT_PATH="${VAULT_PATH%/}"

if [[ ! -d "$VAULT_PATH" ]]; then
  echo "ERROR: Hermes Brain vault not found at: $VAULT_PATH" >&2
  echo "Set OBSIDIAN_VAULT_PATH or create/open the vault first." >&2
  exit 1
fi

cd "$VAULT_PATH"
exec obsidian "$@"
