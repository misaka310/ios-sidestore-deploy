#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <unsigned-app-path> <output-ipa-path>" >&2
}

if [[ $# -ne 2 ]]; then
  usage
  exit 2
fi

APP_INPUT=$1
IPA_INPUT=$2

if [[ ! -d "$APP_INPUT" ]]; then
  echo "Input app bundle does not exist: $APP_INPUT" >&2
  exit 1
fi

APP_PARENT=$(cd "$(dirname "$APP_INPUT")" && pwd -P)
APP_PATH="$APP_PARENT/$(basename "$APP_INPUT")"
APP_NAME=$(basename "$APP_PATH")

if [[ "$APP_NAME" != *.app ]]; then
  echo "Input must be an .app bundle: $APP_PATH" >&2
  exit 1
fi

if [[ ! -f "$APP_PATH/Info.plist" ]]; then
  echo "Input app bundle Info.plist is missing: $APP_PATH/Info.plist" >&2
  exit 1
fi

IPA_PARENT=$(dirname "$IPA_INPUT")
mkdir -p "$IPA_PARENT"
IPA_PARENT=$(cd "$IPA_PARENT" && pwd -P)
IPA_PATH="$IPA_PARENT/$(basename "$IPA_INPUT")"

if [[ -e "$IPA_PATH" || -L "$IPA_PATH" ]]; then
  echo "Output IPA already exists: $IPA_PATH" >&2
  exit 1
fi

STAGING=$(mktemp -d "${TMPDIR:-/tmp}/sidestore-ipa.XXXXXX")
cleanup() {
  rm -rf "$STAGING"
}
trap cleanup EXIT

mkdir -p "$STAGING/Payload"
ditto "$APP_PATH" "$STAGING/Payload/$APP_NAME"

(
  cd "$STAGING"
  COPYFILE_DISABLE=1 zip -q -X -r "$IPA_PATH" Payload
)

echo "Created unsigned IPA: $IPA_PATH"
