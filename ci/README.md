# Isolated single-job runner

`runner.example.toml` is a reviewed starting definition for Forgejo Runner
13.2.0. It is not automatically installed. The coordinator and runner are
separate Silo jails; the runner gets only a private TCP connection to the forge.
Its `host` executor runs inside this jail as the unprivileged Silo workload user.
No host administration, Nix daemon, Docker socket, KVM, or deployment credentials
are granted. A job can read its own runner token, so register it as ephemeral and
scope it to exactly the repository it is allowed to test.

1. As repository owner, create a runner using
   `POST /api/v1/repos/OWNER/REPO/actions/runners` with
   `{"name":"catalogue-ci","ephemeral":true}`. Keep the API authentication
   outside the runner. Store the returned token as the root-owned, mode `0600`
   runtime file `/etc/secrets/silo/credentials/catalogue-ci`; never commit it or
   put it in command arguments. Put only the returned UUID in the definition. Set `CATALOGUE_SILO` to the
   installed, immutable Silo executable path (resolve it on the server with
   `readlink -f /run/current-system/sw/bin/silo`). The validator runs without a
   control socket and does not execute catalogue code or fetch packages.
2. Review the connection service and URL. The example uses the private Silo
   connection to `forgejo:8080`; off-host runners require verified HTTPS and
   explicit network policy. Keep Forgejo's advertised `ROOT_URL` reachable by
   workflows that clone or upload artifacts. Never disable TLS verification.
3. Stop the linked forge while applying a new incoming connection grant, apply
   the reviewed definition using `silo apply`, then restart the forge and run
   `silo run --detach catalogue-ci`. The runner waits for one job, exits after
   it finishes, and Forgejo invalidates its registration. Register and provision
   a fresh ephemeral credential before the next run. Do not enable automatic
   restart with the expired credential.
4. Put `isolation-smoke.yml` under `.forgejo/workflows/` in a test repository
   to verify the boundary. This checks isolation only; it does not validate the
   application catalogue. Copying the example alone does not configure CI.

The tested execution mode is `one-job --wait`. The runner rejects ephemeral
registrations in `daemon` mode. Memory-backed workspaces are discarded when the
jail stops; export required reports before it exits. The repository workflow in `.forgejo/workflows/validate.yml` fetches the exact
triggering commit with its short-lived job token and runs the catalogue validator.
It passed in a disposable guest with a restricted, non-admin repository owner.
The token is passed through Git configuration environment variables, never stored
in the repository URL or Git configuration. Automatic runner allocation, binary
cache verification inside CI, GUI microVM jobs and artifact upload remain to be
implemented and verified.

See the [Forgejo registration documentation](https://forgejo.org/docs/latest/admin/actions/registration/)
for repository scope and server-enforced ephemeral registration semantics.
