#!/usr/bin/env bash
set -euo pipefail

REPO_SLUG="${REPO_SLUG:-microsoft/Loopsbench}"
RUNNER_ROOT="${RUNNER_ROOT:-$HOME/actions-runner-loopsbench}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname)-loopsbench-sandbox}"
RUNNER_LABELS="${RUNNER_LABELS:-loopsbench-sandbox}"
RUNNER_WORKDIR="${RUNNER_WORKDIR:-_work}"
INSTALL_SERVICE="${INSTALL_SERVICE:-true}"

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

need_cmd gh
need_cmd curl
need_cmd tar

mkdir -p "$RUNNER_ROOT"
cd "$RUNNER_ROOT"

asset_url="$(
  gh api repos/actions/runner/releases/latest \
    --jq '.assets[] | select(.name | test("^actions-runner-linux-x64-.*\\.tar\\.gz$")) | .browser_download_url' \
    | head -n1
)"

if [[ -z "$asset_url" ]]; then
  echo "Unable to determine the latest Linux x64 runner download URL." >&2
  exit 1
fi

archive_name="$(basename "$asset_url")"
if [[ ! -f "$archive_name" ]]; then
  curl -fsSL "$asset_url" -o "$archive_name"
fi

if [[ ! -f "./config.sh" ]]; then
  tar xzf "$archive_name"
fi

registration_token="$(
  gh api -X POST "repos/$REPO_SLUG/actions/runners/registration-token" --jq '.token'
)"

if [[ -z "$registration_token" ]]; then
  echo "Failed to obtain a registration token for $REPO_SLUG." >&2
  exit 1
fi

./config.sh \
  --url "https://github.com/$REPO_SLUG" \
  --token "$registration_token" \
  --name "$RUNNER_NAME" \
  --labels "$RUNNER_LABELS" \
  --work "$RUNNER_WORKDIR" \
  --unattended \
  --replace

if [[ "$INSTALL_SERVICE" == "true" ]]; then
  sudo ./svc.sh install
  sudo ./svc.sh start
else
  echo "Runner configured. Start it manually with: $RUNNER_ROOT/run.sh"
fi
