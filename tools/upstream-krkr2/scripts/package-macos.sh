#!/usr/bin/env bash
set -euo pipefail

app="$GITHUB_WORKSPACE/source/out/macos/release/bin/krkr2/krkr2.app"
binary="$app/Contents/MacOS/krkr2"
test -x "$binary"
plutil -lint "$app/Contents/Info.plist"
test "$(/usr/libexec/PlistBuddy -c 'Print CFBundleExecutable' "$app/Contents/Info.plist")" = krkr2
lipo "$binary" -verify_arch arm64

# Copy non-system shared libraries into the bundle and rewrite install names.
cat > "$RUNNER_TEMP/fixup-bundle.cmake" <<'CMAKE'
include(BundleUtilities)
fixup_bundle("$ENV{GITHUB_WORKSPACE}/source/out/macos/release/bin/krkr2/krkr2.app" "" "$ENV{GITHUB_WORKSPACE}/source/out/macos/release/vcpkg_installed/arm64-osx/lib")
CMAKE
cmake -P "$RUNNER_TEMP/fixup-bundle.cmake" 2>&1 | tee logs/bundle.log
python3 tools/upstream-krkr2/scripts/bundle-metadata.py "$app" | tee logs/minimum-macos.txt
codesign --force --deep --sign - "$app"
codesign --verify --deep --strict "$app"
otool -L "$binary" | tee logs/linked-libraries.txt
"$binary" --help 2>&1 | tee logs/help.txt
grep -q 'Usage: krkr2' logs/help.txt

mkdir -p dist
ditto -c -k --sequesterRsrc --keepParent "$app" dist/krkr2-macos-arm64.zip
shasum -a 256 dist/krkr2-macos-arm64.zip > dist/SHA256SUMS.txt
cp source/LICENSE dist/LICENSE.txt
cat > dist/BUILD-INFO.txt <<EOF
Source: https://github.com/2468785842/krkr2
Source revision: $SOURCE_REVISION
Build: https://github.com/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID
Architecture: arm64 (Apple Silicon)
Compiler deployment target: $MACOSX_DEPLOYMENT_TARGET
Minimum macOS version: $(/usr/libexec/PlistBuddy -c 'Print LSMinimumSystemVersion' "$app/Contents/Info.plist")
Signing: ad-hoc; not notarized
Validation: bundle metadata, ARM64 architecture, bundle dependencies, signature, CLI --help
Game compatibility and GUI interaction: not tested
EOF
