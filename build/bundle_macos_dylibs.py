#!/usr/bin/env python3
"""Bundle non-system engine dependencies beside libengine_api.dylib."""

import shutil
import subprocess
import sys
from pathlib import Path


SYSTEM_PREFIXES = ("/System/Library/", "/usr/lib/")


def run(*args):
    return subprocess.check_output(args, text=True)


def dependencies(dylib):
    lines = run("otool", "-L", str(dylib)).splitlines()
    # The first entry of a dylib is its own install name.
    return [line.strip().split(" (", 1)[0] for line in lines[2:]]


def main(app):
    frameworks = app / "Contents" / "Frameworks"
    engine = frameworks / "libengine_api.dylib"
    if not engine.is_file():
        raise RuntimeError(f"Engine library is missing: {engine}")

    bundled = {engine.name: engine}
    origins = {engine.name: engine.resolve()}
    pending = [engine]
    scanned = set()

    while pending:
        dylib = pending.pop()
        if dylib in scanned:
            continue
        scanned.add(dylib)

        for dep in dependencies(dylib):
            if dep.startswith(SYSTEM_PREFIXES) or dep.startswith("@"):
                continue
            source = Path(dep)
            if not source.is_absolute():
                raise RuntimeError(f"Unrecognized library reference in {dylib}: {dep}")
            if not source.is_file():
                raise RuntimeError(f"Required library is missing: {dep}")

            name = source.name
            destination = frameworks / name
            resolved = source.resolve()
            if name in origins and origins[name] != resolved:
                raise RuntimeError(f"Conflicting libraries named {name}: {origins[name]} and {resolved}")
            if name not in origins:
                shutil.copy2(source, destination)
                origins[name] = resolved
                bundled[name] = destination
                pending.append(destination)
                print(f"Bundled {dep} as {destination}")

            subprocess.check_call(
                ["install_name_tool", "-change", dep, f"@loader_path/{name}", str(dylib)]
            )

    for name, dylib in bundled.items():
        if dylib != engine:
            subprocess.check_call(["install_name_tool", "-id", f"@loader_path/{name}", str(dylib)])
        for dep in dependencies(dylib):
            if dep.startswith("/") and not dep.startswith(SYSTEM_PREFIXES):
                raise RuntimeError(f"External dependency remains in {dylib}: {dep}")
        subprocess.check_call(["codesign", "--force", "--sign", "-", str(dylib)])

    print(f"Verified {len(bundled)} bundled engine libraries")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: bundle_macos_dylibs.py <app bundle>")
    main(Path(sys.argv[1]).resolve())
