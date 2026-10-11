# Silo application catalogue

Reviewable application definitions for Silo. This catalogue is external data, not part of the client binary. Package references are pinned to a Nixpkgs commit. Networked applications default to VPN and offline tools default to blocked networking.

## Status

These entries are candidates undergoing runtime acceptance. A schema pass or package build is not a runtime pass. VPN port-forwarding integration and representative interaction tests are required before the torrent entries are considered ready.

## Review and install

Add this Git repository through Silo’s source settings, refresh it, then browse the app catalogue. Review the exact revision, permissions, package reference, options, and effective configuration before accepting installation. Source refresh does not update installed applications.

The command-line equivalents are `silo source add`, `silo source refresh`, `silo preset search`, `silo preset show`, `silo preset review`, and `silo preset install`. Run each command with `--help` for its arguments. Source URLs belong in private runtime configuration.

## Format and contributions

`catalogue.json` contains versioned metadata, complete jail definitions, typed option choices, and smoke-test descriptors. Icons are names from the installed desktop icon theme; no third-party icon artwork is redistributed. Application licenses in metadata describe upstream software; confirm the pinned package’s complete license information before redistribution.

Custom hooks live in the jail definition and execute inside the jail. They are executable code and must be reviewed, including on updates. Never put credentials in this catalogue. Grant only the resources an application needs, and test all changed entries in disposable guests.

The initial test descriptors include readiness checks. They must be augmented with representative fixture-based operations for release acceptance; `--version` alone is insufficient.

## Binary-cache requirement

Every listed package, including its complete installable dependency closure, must
be available from `https://cache.nixos.org`. Run `python3 check-cache.py` before
publishing catalogue changes. This queries cache metadata without building or
realising anything and disables import-from-derivation during evaluation. A
failure excludes the entry; do not compile it locally to make the check pass or
use a different cache. Recheck when changing a package pin. Cache availability
can change after publication, so clients should use substitution-only Nix settings
when source compilation is not acceptable.

## Runtime verification

`runtime-verification.json` records startup checks for all 29 entries in a
disposable guest. GUI captures were inspected, including document/image fixtures
and the torrent client main window. These checks use a local VPN fixture; they
do not certify live-provider transfers or physical-GPU behavior. Kate stays in
the foreground for supervision. The incoming-port wrappers for qBittorrent and
Transmission CLI consume the exclusive port supplied by Silo.
