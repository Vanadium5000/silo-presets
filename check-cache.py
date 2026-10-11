#!/usr/bin/env python3
"""Reject catalogue entries whose installable closure is not in cache.nixos.org.

Read-only: evaluates pinned package outputs and queries binary-cache metadata.
Never realises packages, invokes nix build, or falls back to another cache.
"""
import json
from pathlib import Path
import subprocess
import sys


def query(arguments):
    result = subprocess.run(
        ["nix", "--option", "allow-import-from-derivation", "false", *arguments],
        capture_output=True, text=True, timeout=180, check=True,
    )
    return json.loads(result.stdout)


def main():
    catalogue = json.loads(Path(__file__).with_name("catalogue.json").read_text())
    failed = []
    for app in catalogue["apps"]:
        try:
            outputs = query([
                "eval", "--json", app["jail"]["command"]["installable"], "--apply",
                'p: map (name: p.${name}.outPath) (p.meta.outputsToInstall or [p.outputName])',
            ])
            closure = query([
                "path-info", "--store", "https://cache.nixos.org", "--recursive",
                "--json", *outputs,
            ])
            if not closure:
                raise ValueError("empty package closure")
            print(f"PASS {app['id']}: {len(closure)} cached paths", flush=True)
        except (subprocess.SubprocessError, ValueError, KeyError) as error:
            # Do not dump remote-source arguments or subprocess output.
            print(f"FAIL {app['id']}: cache verification failed ({type(error).__name__})", flush=True)
            failed.append(app["id"])
    return bool(failed)


if __name__ == "__main__":
    sys.exit(main())
