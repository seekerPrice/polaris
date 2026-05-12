#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/veeainc/lobstertrap.git"
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

git clone --depth 1 "$REPO_URL" "$TMPDIR/lobstertrap"
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
