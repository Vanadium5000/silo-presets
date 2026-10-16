# Silo application catalogue

Reviewable application definitions for Silo. This catalogue is external data, not part of the client binary. Package references are pinned to a Nixpkgs commit. Networked applications default to VPN and offline tools default to blocked networking.

## Status

All 29 entries have recorded startup checks. All five torrent entries additionally
have live VPN transfer and inbound-port evidence in [torrent-verification.json](torrent-verification.json).
This establishes the tested versions and conditions, not every application feature
or future provider/network behavior.

## Review and install

Add this Git repository through Silo’s source settings, then browse the app catalogue. Current Silo versions populate uncached libraries automatically; use Refresh to check for later revisions. Review the exact revision, permissions, package reference, options, and effective configuration before accepting installation. Source refresh does not update installed applications.

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
the foreground for supervision. All five incoming-port wrappers consume the exclusive port supplied by Silo;
the separate live-transfer report records their subsequent checks.

## Forwarded torrent applications

All five torrent entries require VPN port forwarding and use the in-jail
`/run/silo/torrent` adapter from Silo. Install a Silo version providing this adapter
before updating these definitions; older versions fail closed at startup.
The reviewed wrappers pass arguments without shell interpolation. Each launch
validates and applies the exclusive provider port. Transmission Qt preserves its
4.1 JSON preferences; qBittorrent preserves its INI preferences. Both disable
UPnP/NAT-PMP. aria2 and rTorrent also use the forwarded UDP port for DHT.
rTorrent loads existing preferences before enforcing the leased port and keeps a private session directory for DHT state.
The adapter does not grant networking or weaken jail limits.

Stop a torrent app before claiming its tunnel's port for another app. An expired
lease or replaced tunnel requires restarting the app. Changing the listening
port in the application can break inbound connectivity until the next launch.
Full transfer, incoming-peer and throughput measurements are recorded separately
in [torrent-verification.json](torrent-verification.json), including resumed-check
distinctions and network comparison limits.

## Hosting services

The seven private hosting presets and their required Silo capabilities are
explained in [HOSTING.md](HOSTING.md), including HTTPS routing, credential
provisioning, monitoring and backup setup. Review this guide before publishing
ports. Hosting verification is separate from the original desktop catalogue.
