#!/usr/bin/env python3
"""Match the app's minimum macOS version to its bundled ARM64 binaries."""

import plistlib
import struct
import sys
from pathlib import Path


def minimum_macos(path):
    data = path.read_bytes()
    if len(data) < 32 or struct.unpack_from('<II', data) != (0xFEEDFACF, 0x100000C):
        raise ValueError(f'Expected a thin ARM64 Mach-O binary: {path}')
    offset = 32
    minimum = None
    for _ in range(struct.unpack_from('<I', data, 16)[0]):
        command, size = struct.unpack_from('<II', data, offset)
        if size < 8 or offset + size > len(data):
            raise ValueError(f'Invalid Mach-O load command: {path}')
        if command == 0x32:  # LC_BUILD_VERSION
            platform, version = struct.unpack_from('<II', data, offset + 8)
            if platform != 1:  # PLATFORM_MACOS
                raise ValueError(f'Expected a macOS binary: {path}')
            minimum = version
        elif command == 0x24:  # LC_VERSION_MIN_MACOSX
            minimum = struct.unpack_from('<I', data, offset + 8)[0]
        offset += size
    if minimum is None:
        raise ValueError(f'Missing minimum macOS version: {path}')
    return minimum >> 16, (minimum >> 8) & 255, minimum & 255


def main():
    app = Path(sys.argv[1])
    plist_path = app / 'Contents/Info.plist'
    plist = plistlib.loads(plist_path.read_bytes())
    binary = app / 'Contents/MacOS' / plist['CFBundleExecutable']
    libraries = sorted((app / 'Contents/Frameworks').rglob('*.dylib'))
    minimum = tuple(map(int, plist['LSMinimumSystemVersion'].split('.')))
    for path in [binary, *libraries]:
        if path.is_symlink():
            continue
        version = minimum_macos(path)
        minimum = max(minimum, version)
        print(f'{path.relative_to(app)}: minimum macOS {".".join(map(str, version))}')
    plist['LSMinimumSystemVersion'] = '.'.join(map(str, minimum))
    plist_path.write_bytes(plistlib.dumps(plist, sort_keys=False))
    print(f'Application minimum macOS: {plist["LSMinimumSystemVersion"]}')


if __name__ == '__main__':
    main()
