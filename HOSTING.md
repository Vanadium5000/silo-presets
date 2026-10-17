# Hosting presets

These presets require Silo's `hosting-v1` and `runtime-credentials-v1`
capabilities (`silo capabilities --json`). Install the updated Silo release
before importing them. They are private starting configurations: none publishes
a host port or grants host administration. Review storage, backups, credentials,
networking and application configuration before exposing a service.

| Preset | Private endpoint | Persistent data | Additional setup |
| --- | --- | --- | --- |
| Vaultwarden | 8080 | `/state/home/data` | Native clients/API; web vault disabled, registration disabled. Configure the public HTTPS domain and reviewed account provisioning. |
| Forgejo | 8080 | `/state/home` | Private HTTP Git and Actions coordinator; registration and SSH disabled. CLI administrator setup and private HTTPS required. |
| Jellyfin | 8096 | `/state/home/{data,config,cache,log}` | Attach a media volume read-only; complete its setup wizard privately. GPU acceleration requires a separately reviewed device grant. |
| Traefik | 8080 ping, 8443 TLS | `/state/home` | Configure routes, backend grants and certificate resolver; no dashboard exposed. |
| nginx | 8080 health | `/state/home` | Configure routes and certificate volume/client; no default site content. |
| PostgreSQL | 5432 | `/state/home/data` | Provision `postgresql-password`; local socket trust is confined to this jail, TCP requires SCRAM. |
| Prometheus | 9090 | `/state/home/data` | Add explicit service connections, scrape targets and rules. |
| Alertmanager | 9093 | `/state/home/data` | Add a receiver and explicit outbound access or private webhook connection. The initial receiver deliberately sends nothing. |

All have restart limits and private persistent homes. Adjust quotas for real
data: the initial allocation is not a media-library or database capacity plan.
Include both the private home and every attached volume in a Backkeep job. Use
`stop_consumers = true` for consistent scheduled filesystem snapshots; verify
restores before relying on a backup. PostgreSQL logical backups require its own
dump tools. Package rollback is disabled until an administrator explicitly
approves compatibility with the application's persistent data format.

## HTTPS proxy example

After importing Vaultwarden and Traefik, stop both while editing their reviewed
jail definitions. Add a Traefik `hosting.connect` grant for service `vaultwarden`,
TCP 8080. Publish host TCP 443 to Traefik 8443 on each required address family.
For an HTTP challenge, also publish TCP 80 to Traefik 8080. The initial ping endpoint shares port 8080. To keep it private when publishing
HTTP 80, add an unpublished `health` entry point (for example `:8082`) and change
the existing `[ping]` section to `entryPoint = "health"`. Do not expose an
administration dashboard.

Add a certificate resolver to `traefik.toml` (replace the example address):

```toml
[certificatesResolvers.public.acme]
email = "operator@example.org"
storage = "/state/home/acme.json"
[certificatesResolvers.public.acme.httpChallenge]
entryPoint = "web"
```

Replace `routes.toml` with reviewed routes:

```toml
[http.routers.vault]
rule = "Host(`vault.example.org`)"
entryPoints = ["websecure"]
service = "vault"
[http.routers.vault.tls]
certResolver = "public"
[[http.services.vault.loadBalancer.servers]]
url = "http://vaultwarden:8080"
```

Set Vaultwarden's `DOMAIN` to the same public HTTPS URL. DNS and the provider
firewall must point at this host. Keep Traefik's ACME state persistent and backed
up. Use the ACME staging directory while testing issuance to avoid production
rate limits. See [Traefik ACME documentation](https://doc.traefik.io/traefik/https/acme/)
for DNS providers and credential-file support. Grant only the selected provider's
credential; never commit its value to this repository or a jail definition.

## Monitoring

Run Silo's `silo-exporter` in a separate jail with the read-only `host-metrics`
grant, then grant Prometheus a connection to its private TCP 9108 endpoint.
Grant Prometheus a connection to Alertmanager TCP 9093. Store scrape/rule files
in reviewed application configuration and delivery secrets under
`/run/credentials`. Configure external receivers using
[Alertmanager's receiver documentation](https://prometheus.io/docs/alerting/latest/configuration/).
The application owns alert evaluation and delivery; Silo only supplies isolation,
storage, connectivity and read-only metrics access.

## Deployment

For custom Nix applications, use Silo's scoped mTLS `silo.deploy:APP` identities,
signed administrator-approved caches and retained immutable releases. These
identities cannot edit the grants in these presets. A health command and reviewed
data compatibility are required for automated release rollback. Application
upgrades that migrate data need a separate backup and maintenance procedure.

Runtime verification is recorded separately. Readiness and restart checks are
not certification of public ACME renewal, hardware transcoding or disaster
recovery for every upstream application version.

## Private Forgejo

Forgejo also requires Silo's `env-shebang-v1` capability for generated Git hooks.
Check `silo capabilities --json` before importing it; older hosts can pass an HTTP
health check but fail repository creation and Git pushes without this support.

The Forgejo preset grants no host ports, outbound network, runner execution, or
host administration. Its runtime configuration is copied once into its persistent
home and contains generated application secrets after first start. Later preset
changes do not overwrite that file. Review and edit `/state/home/app.ini` during
maintenance, setting `[server] ROOT_URL` to the chosen private HTTPS URL.
Create the first administrator with Forgejo's CLI inside the jail; registration
and the installation wizard are disabled. Keep administrator passwords out of
shell history and process arguments by using the CLI's generated-password flow
and immediately storing the result in your vault.

Grant a private TLS proxy access to TCP 8080. Bind ingress only to the chosen
WireGuard address and use a private CA trusted by enrolled desktops. Git over
HTTPS needs no host SSH service. The preset does not install a CA or configure
DNS; those are deployment-specific choices.

Register a separate, repository-scoped Actions runner. Do not execute jobs in
the forge's jail or give runners its database, signing secrets, administrator
tokens, backup credentials, or the Silo administration socket. Use separate
scoped deployment credentials only for jobs that need release access. Actions
are resolved against this forge by default; import and pin any required actions
before enabling workflows. Software-emulated GUI guests should have explicit
memory, CPU and timeout limits on providers without nested KVM.

Back up the entire persistent home with consumers stopped, including the SQLite
database, repository files, generated secrets, LFS data and Actions artifacts.
Test a restore into a separate private jail before upgrading. An application
binary rollback alone cannot undo a database migration.

Forgejo API/Git and automatic local backup/restore results are recorded in
[forgejo-verification.json](forgejo-verification.json), including their limits.
For same-server backups, use Backkeep's protected
`/var/lib/backkeep/repositories/NAME` location with the actual persistent
filesystem UUID. Set `schedule_seconds = 21600`, `retention_days = 30`,
`auto_clean = true`, and `stop_consumers = true`. This requires the Backkeep
release supporting server-local repositories; no removable drive is needed.
Keep an independent backup copy when ready, because local backups share the
server's disk and failure domain.

A tested single-job runner definition and its isolation smoke workflow are in
[ci/](ci/README.md). Catalogue validation also passed using the exact commit and a scoped job token.
Runner allocation, cache verification inside CI and GUI testing are not yet
automated; the verification record distinguishes this coverage.
