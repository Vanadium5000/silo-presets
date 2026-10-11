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
