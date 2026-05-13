#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/veeainc/lobstertrap.git"
# Phase-10 T2.2: pin to a known-good upstream commit so fresh clones build the same
# binary that passes our 11/11 corpus tests + closed-loop demo. Captured 2026-05-13.
# To bump: clone upstream fresh, run `./bin/lobstertrap test` against our policies,
# then update this SHA and re-run all live e2e tests.
LT_PINNED_SHA="e49a402864104c19c9a560ad73e06d5493e5d876"
TMPDIR="$(mktemp -d)"
TARGET="./bin/lobstertrap"
DEFAULT_POLICY_TARGET="./examples/lobstertrap_default_policy.yaml"

mkdir -p ./bin ./examples

uname_s="$(uname -s)"
case "$uname_s" in
  Darwin) BUILD_TARGET="build-darwin" ;;
  Linux)  BUILD_TARGET="build-linux"  ;;
  *) echo "Unsupported OS: $uname_s" >&2; exit 1 ;;
esac

# Full clone (not --depth 1) so we can checkout the pinned SHA.
git clone "$REPO_URL" "$TMPDIR/lobstertrap"
git -C "$TMPDIR/lobstertrap" checkout "$LT_PINNED_SHA"
echo "[download_lobstertrap] checked out pinned SHA: $LT_PINNED_SHA"
pushd "$TMPDIR/lobstertrap" >/dev/null

# Try plain `make build` first — produces ./lobstertrap (no suffix). Falls back to OS-specific
# targets (produce ./lobstertrap-darwin-arm64 / ./lobstertrap-linux-amd64), then go build directly.
if make -n build >/dev/null 2>&1; then
  make build
elif make -n "$BUILD_TARGET" >/dev/null 2>&1; then
  make "$BUILD_TARGET"
else
  go build -o lobstertrap .
fi

# Locate the binary. Names observed in the wild: lobstertrap, lobstertrap-darwin-arm64,
# lobstertrap-linux-amd64, build/<os>/<arch>/lobstertrap.
BIN=""
for cand in \
  ./lobstertrap \
  ./lobstertrap-darwin-arm64 \
  ./lobstertrap-linux-amd64 \
  ./build/darwin/arm64/lobstertrap \
  ./bin/lobstertrap \
  ./dist/lobstertrap-darwin-arm64; do
  if [[ -f "$cand" ]]; then BIN="$cand"; break; fi
done
if [[ -z "$BIN" ]]; then
  BIN="$(find . -maxdepth 4 -type f \( -name 'lobstertrap' -o -name 'lobstertrap-*' \) -perm -u=x 2>/dev/null | head -n1 || true)"
fi
if [[ -z "$BIN" ]]; then echo "Could not locate built binary" >&2; ls -R; exit 2; fi
popd >/dev/null

cp "$TMPDIR/lobstertrap/$BIN" "$TARGET"
chmod +x "$TARGET"

# Default policy for schema reference + before/after diff in the pitch
if [[ -f "$TMPDIR/lobstertrap/configs/default_policy.yaml" ]]; then
  cp "$TMPDIR/lobstertrap/configs/default_policy.yaml" "$DEFAULT_POLICY_TARGET"
fi

rm -rf "$TMPDIR"

"$TARGET" version
